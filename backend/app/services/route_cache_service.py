import os
import time
import copy
import logging
import threading
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from pymongo import MongoClient, UpdateOne
from pymongo.errors import PyMongoError, DuplicateKeyError

from ..schemas.route import RoutingTier, WalkingSource
from ..core.database import MONGODB_URL, DB_NAME

logger = logging.getLogger("voyantra.route_cache")

CACHE_VERSION = "v1"
CACHE_COLLECTION = "route_cache"
TTL_SECONDS = 604800  # 7 days
MONGO_CIRCUIT_COOLDOWN = 60.0
MAX_UPGRADE_ATTEMPTS = 3


class SingleFlight:
    """
    Thread-safe request coalescer.
    Ensures identical concurrent cache-miss calculations execute exactly once.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._calls: Dict[str, Tuple[threading.Event, Dict[str, Any]]] = {}

    def execute(self, key: str, func, *args, **kwargs):
        with self._lock:
            if key in self._calls:
                event, box = self._calls[key]
                is_leader = False
            else:
                event = threading.Event()
                box = {"result": None, "error": None}
                self._calls[key] = (event, box)
                is_leader = True

        if not is_leader:
            event.wait()
            if box["error"] is not None:
                raise box["error"]
            return copy.deepcopy(box["result"])

        try:
            res = func(*args, **kwargs)
            box["result"] = res
            return res
        except Exception as exc:
            box["error"] = exc
            raise exc
        finally:
            with self._lock:
                self._calls.pop(key, None)
            event.set()


class RouteCacheService:
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db = None
        self.single_flight = SingleFlight()

        # MongoDB circuit breaker state
        self._mongo_circuit_open: bool = False
        self._mongo_fail_count: int = 0
        self._mongo_opened_at: float = 0.0

        self._init_mongo_client()

    def _init_mongo_client(self):
        try:
            timeout_ms = 5000 if "mongodb+srv" in MONGODB_URL else 1000
            self.client = MongoClient(
                MONGODB_URL,
                serverSelectionTimeoutMS=timeout_ms,
                connectTimeoutMS=timeout_ms,
                socketTimeoutMS=timeout_ms
            )
            self.db = self.client[DB_NAME]
            self.ensure_indexes()
        except Exception as e:
            logger.warning(f"[RouteCacheService] Mongo client init notice ({e}). Operating resiliently.")

    def ensure_indexes(self):
        """Idempotent index setup for route_cache collection."""
        if not self._check_mongo_circuit() or self.db is None:
            return
        try:
            col = self.db[CACHE_COLLECTION]
            col.create_index("cache_key", unique=True)
            col.create_index("created_at", expireAfterSeconds=TTL_SECONDS)
            col.create_index([("namespace", 1), ("cache_version", 1)])
            self._record_mongo_success()
        except Exception as e:
            self._record_mongo_failure(e)
            logger.warning(f"[RouteCacheService] ensure_indexes error: {e}")

    # -------------------------------------------------------------------------
    # Circuit Breaker Helpers
    # -------------------------------------------------------------------------
    def _check_mongo_circuit(self) -> bool:
        if self._mongo_circuit_open:
            if time.time() - self._mongo_opened_at > MONGO_CIRCUIT_COOLDOWN:
                self._mongo_circuit_open = False
                self._mongo_fail_count = 0
                return True
            return False
        return True

    def _record_mongo_failure(self, err: Exception):
        self._mongo_fail_count += 1
        logger.warning(f"[RouteCacheService] MongoDB error (#{self._mongo_fail_count}): {err}")
        if self._mongo_fail_count >= 3:
            self._mongo_circuit_open = True
            self._mongo_opened_at = time.time()
            logger.error("[RouteCacheService] MongoDB circuit breaker OPENED for 60s.")

    def _record_mongo_success(self):
        self._mongo_fail_count = 0
        self._mongo_circuit_open = False

    # -------------------------------------------------------------------------
    # Key Formatters
    # -------------------------------------------------------------------------
    @staticmethod
    def format_route_key(o_lat: float, o_lng: float, d_lat: float, d_lng: float, mode: str) -> str:
        return f"{CACHE_VERSION}:route:{o_lat:.5f},{o_lng:.5f}:{d_lat:.5f},{d_lng:.5f}:{mode}"

    @staticmethod
    def format_cell_key(o_lat: float, o_lng: float, d_lat: float, d_lng: float, mode: str) -> str:
        return f"{CACHE_VERSION}:cell:{o_lat:.5f},{o_lng:.5f}:{d_lat:.5f},{d_lng:.5f}:{mode}"

    # -------------------------------------------------------------------------
    # Route Cache Operations
    # -------------------------------------------------------------------------
    def get_cached_route(
        self,
        o_lat: float,
        o_lng: float,
        d_lat: float,
        d_lng: float,
        mode: str,
        fossgis_foot_healthy: bool = True,
        tier1_healthy: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Lookup cached route. Handles upgrade triggers (soft miss) and anti-loop retry ceilings.
        """
        if not self._check_mongo_circuit() or self.db is None:
            return None

        key = self.format_route_key(o_lat, o_lng, d_lat, d_lng, mode)
        try:
            doc = self.db[CACHE_COLLECTION].find_one({"cache_key": key, "namespace": "route"})
            self._record_mongo_success()
            if not doc:
                return None

            # Ignore entries from previous cache versions
            if doc.get("cache_version") != CACHE_VERSION:
                return None

            tier = doc.get("tier_used")
            walking_source = doc.get("walking_source")
            attempts = doc.get("upgrade_attempts", 0)

            # Quality Upgrade Trigger 1: Walking entry is corrected_car, and FOSSGIS foot is healthy
            if mode == "walking" and walking_source == WalkingSource.corrected_car.value and fossgis_foot_healthy:
                if attempts < MAX_UPGRADE_ATTEMPTS:
                    logger.info(f"[RouteCacheService] Soft miss: Upgrading corrected_car -> fossgis_foot (attempt {attempts + 1})")
                    self._increment_upgrade_attempt(key, attempts)
                    return None

            # Quality Upgrade Trigger 2: Entry is public_demo, and Tier 1 (local_osrm) is up
            if tier == RoutingTier.public_demo.value and tier1_healthy:
                if attempts < MAX_UPGRADE_ATTEMPTS:
                    logger.info(f"[RouteCacheService] Soft miss: Upgrading public_demo -> local_osrm (attempt {attempts + 1})")
                    self._increment_upgrade_attempt(key, attempts)
                    return None

            return doc
        except PyMongoError as e:
            self._record_mongo_failure(e)
            return None
        except Exception as e:
            logger.warning(f"[RouteCacheService] get_cached_route error: {e}")
            return None

    def _increment_upgrade_attempt(self, key: str, current_attempts: int):
        try:
            self.db[CACHE_COLLECTION].update_one(
                {"cache_key": key},
                {
                    "$set": {
                        "upgrade_attempts": current_attempts + 1,
                        "last_upgrade_attempt": datetime.now(timezone.utc)
                    }
                }
            )
        except Exception:
            pass

    def save_route(
        self,
        o_lat: float,
        o_lng: float,
        d_lat: float,
        d_lng: float,
        mode: str,
        distance_km: float,
        raw_duration_min: float,
        tier_used: RoutingTier,
        walking_source: Optional[WalkingSource],
        polyline_geojson: Dict[str, Any],
        steps: List[Any]
    ) -> bool:
        """
        Persist computed route. Enforces:
        1. Pure raw OSRM values stored
        2. TIER 3 RESULTS (haversine_detour) ARE NEVER PERSISTED
        3. Stored geometry is [[lat, lon], ...]
        4. created_at reset on upsert
        5. DuplicateKeyError safely handled
        """
        # CRITICAL RULE: Never store Tier 3 (haversine_detour) results
        if tier_used == RoutingTier.haversine_detour or tier_used.value == "haversine_detour":
            logger.debug("[RouteCacheService] Skipping cache write for Tier 3 haversine_detour")
            return False

        if not self._check_mongo_circuit() or self.db is None:
            return False

        key = self.format_route_key(o_lat, o_lng, d_lat, d_lng, mode)

        # Standardize steps format
        formatted_steps = []
        for s in steps:
            if hasattr(s, "model_dump"):
                formatted_steps.append(s.model_dump())
            elif isinstance(s, dict):
                formatted_steps.append(s)

        doc = {
            "cache_key": key,
            "namespace": "route",
            "cache_version": CACHE_VERSION,
            "origin": {"lat": round(o_lat, 5), "lng": round(o_lng, 5)},
            "destination": {"lat": round(d_lat, 5), "lng": round(d_lng, 5)},
            "mode": mode,
            "distance_km": round(distance_km, 3),
            "raw_duration_min": round(raw_duration_min, 1),
            "tier_used": tier_used.value,
            "walking_source": walking_source.value if walking_source else None,
            "polyline_geojson": polyline_geojson,
            "turn_by_turn_steps": formatted_steps,
            "upgrade_attempts": 0,
            "created_at": datetime.now(timezone.utc)
        }

        try:
            self.db[CACHE_COLLECTION].update_one(
                {"cache_key": key},
                {"$set": doc},
                upsert=True
            )
            self._record_mongo_success()
            return True
        except DuplicateKeyError:
            # Benign concurrent insert race condition
            return True
        except PyMongoError as e:
            self._record_mongo_failure(e)
            return False
        except Exception as e:
            logger.warning(f"[RouteCacheService] save_route write error: {e}")
            return False

    # -------------------------------------------------------------------------
    # Matrix Cell Operations
    # -------------------------------------------------------------------------
    def get_cached_cells(self, keys: List[str]) -> Dict[str, Dict[str, Any]]:
        """Batch lookup for matrix cells with namespace 'cell'."""
        if not self._check_mongo_circuit() or self.db is None or not keys:
            return {}

        try:
            cursor = self.db[CACHE_COLLECTION].find({
                "cache_key": {"$in": keys},
                "namespace": "cell",
                "cache_version": CACHE_VERSION
            })
            self._record_mongo_success()
            return {doc["cache_key"]: doc for doc in cursor}
        except PyMongoError as e:
            self._record_mongo_failure(e)
            return {}
        except Exception as e:
            logger.warning(f"[RouteCacheService] get_cached_cells error: {e}")
            return {}

    def save_matrix_cells(
        self,
        cells: List[Dict[str, Any]]
    ):
        """
        Bulk upsert newly computed matrix cells.
        Omits any cell that used haversine_detour.
        """
        if not self._check_mongo_circuit() or self.db is None or not cells:
            return

        operations = []
        for c in cells:
            tier = c.get("tier_used")
            tier_val = tier.value if hasattr(tier, "value") else str(tier)
            # CRITICAL RULE: Never persist Tier 3 matrix cells
            if tier_val == RoutingTier.haversine_detour.value:
                continue

            ws = c.get("walking_source")
            ws_val = ws.value if hasattr(ws, "value") else ws

            doc = {
                "cache_key": c["cache_key"],
                "namespace": "cell",
                "cache_version": CACHE_VERSION,
                "origin": {"lat": round(c["origin_lat"], 5), "lng": round(c["origin_lng"], 5)},
                "destination": {"lat": round(c["dest_lat"], 5), "lng": round(c["dest_lng"], 5)},
                "mode": c["mode"],
                "distance_km": round(c["distance_km"], 3),
                "duration_min": round(c["duration_min"], 1),
                "tier_used": tier_val,
                "walking_source": ws_val,
                "created_at": datetime.now(timezone.utc)
            }
            operations.append(
                UpdateOne(
                    {"cache_key": c["cache_key"]},
                    {"$set": doc},
                    upsert=True
                )
            )

        if operations:
            try:
                self.db[CACHE_COLLECTION].bulk_write(operations, ordered=False)
                self._record_mongo_success()
            except PyMongoError as e:
                self._record_mongo_failure(e)
            except Exception as e:
                logger.warning(f"[RouteCacheService] bulk_write cells error: {e}")

    # -------------------------------------------------------------------------
    # Read-Time Festival Closure Check
    # -------------------------------------------------------------------------
    def check_festival_closures(
        self,
        polyline_coords: List[List[float]],
        city_id: str,
        travel_date: Optional[str]
    ) -> Tuple[bool, Optional[str], List[str]]:
        """
        Read-time festival road closure inspection.
        Intersects route polyline [[lat, lon], ...] against active Phase 3 festival closures.
        """
        if not travel_date or not polyline_coords:
            return False, None, []

        try:
            festivals_col = self.db["festivals"] if self.db is not None else None
            if festivals_col is None:
                return False, None, []

            # Find festivals in city spanning travel_date
            matching = list(festivals_col.find({
                "city_id": city_id,
                "start_date": {"$lte": travel_date},
                "end_date": {"$gte": travel_date}
            }))

            affected_events = []
            for fest in matching:
                closures = fest.get("road_closures", [])
                fest_name = fest.get("name", "Festival Event")
                # Check each closure zone / point
                for cl in closures:
                    cl_coords = cl.get("coordinates", [])
                    # Coordinates could be a point [lat, lon] or polyline/polygon
                    for pt in cl_coords:
                        if len(pt) >= 2:
                            cl_lat, cl_lon = pt[0], pt[1]
                            # Check proximity to any polyline vertex (< 150m ~ 0.0014 deg)
                            for r_pt in polyline_coords:
                                if len(r_pt) >= 2:
                                    if abs(r_pt[0] - cl_lat) < 0.0015 and abs(r_pt[1] - cl_lon) < 0.0015:
                                        if fest_name not in affected_events:
                                            affected_events.append(fest_name)
                                        break

            if affected_events:
                warning = f"Notice: Route intersects active festival road closure zones for: {', '.join(affected_events)}."
                return True, warning, affected_events

            return False, None, []
        except Exception as e:
            logger.debug(f"[RouteCacheService] check_festival_closures notice: {e}")
            return False, None, []


route_cache_service = RouteCacheService()
