import json
import logging
import threading
import time
import urllib.request
import urllib.error
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from ..core.config import settings
from ..core.geo import (
    haversine_km,
    get_detour_factor,
    estimate_road_distance_km,
    estimate_travel_time_minutes,
    DEFAULT_WALKING_SPEED_KMH,
    DEFAULT_DRIVING_SPEED_KMH,
)
from ..schemas.place import Coordinates
from ..schemas.route import (
    RouteRequest,
    RouteResponse,
    RouteMatrixRequest,
    RouteMatrixResponse,
    TurnStep,
    RouteModeEnum,
    RoutingTier,
    WalkingSource,
)
from .route_cache_service import route_cache_service

logger = logging.getLogger(__name__)

# Standard pedestrian speed: 1.25 m/s = 4.5 km/h
PEDESTRIAN_SPEED_MS = 1.25

# OSM Foundation Compliance User-Agent (ODbL / OSRM Attribution compliant)
OSRM_USER_AGENT = "Voyantra-Travel-Planner/1.0 (Academic Research & Travel Planning Demo)"

# Public OSRM Demo Endpoints
OSRM_DEMO_DRIVING_URL = "http://router.project-osrm.org"
OSRM_FOSSGIS_FOOT_URL = "https://routing.openstreetmap.de/routed-foot"

# Global Outbound Throttle Configuration (~1 request/second)
_tier2_throttle_lock = threading.Lock()
_tier2_next_available_time: float = 0.0
TIER2_MIN_REQUEST_INTERVAL: float = 1.0   # Enforce at least 1.0s between outbound requests
MAX_THROTTLE_WAIT_SECONDS: float = 2.5    # Max queue wait time before immediately cascading to Tier 3

# Tier 1 Circuit Breaker (skips Tier 1 when offline to prevent ~0.8s local socket timeouts)
_tier1_circuit_open: bool = False
_tier1_circuit_opened_at: float = 0.0
TIER1_CIRCUIT_COOLDOWN_SECONDS: float = 45.0


class Tier2ThrottleExceeded(Exception):
    """Raised when queue wait for public demo exceeds MAX_THROTTLE_WAIT_SECONDS."""
    pass


def _acquire_tier2_slot() -> None:
    """
    Reserve an outbound dispatch slot for Tier 2 public demo.
    If the queue delay would exceed MAX_THROTTLE_WAIT_SECONDS, instantly raises
    Tier2ThrottleExceeded without sleeping, allowing immediate fallback to Tier 3.
    """
    global _tier2_next_available_time
    with _tier2_throttle_lock:
        now = time.time()
        scheduled_time = max(now, _tier2_next_available_time)
        wait_needed = scheduled_time - now

        if wait_needed > MAX_THROTTLE_WAIT_SECONDS:
            raise Tier2ThrottleExceeded(
                f"Queue wait ({wait_needed:.2f}s) exceeds max threshold ({MAX_THROTTLE_WAIT_SECONDS}s)"
            )

        _tier2_next_available_time = scheduled_time + TIER2_MIN_REQUEST_INTERVAL

    # Sleep outside the lock so other threads can inspect the queue non-blockingly
    if wait_needed > 0:
        time.sleep(wait_needed)


def _throttle_tier2_call():
    """Backward-compatible alias for acquiring a Tier 2 request slot."""
    _acquire_tier2_slot()


def _is_tier1_healthy() -> bool:
    global _tier1_circuit_open, _tier1_circuit_opened_at
    if _tier1_circuit_open:
        if time.time() - _tier1_circuit_opened_at > TIER1_CIRCUIT_COOLDOWN_SECONDS:
            _tier1_circuit_open = False
            return True
        return False
    return True


def _record_tier1_failure():
    global _tier1_circuit_open, _tier1_circuit_opened_at
    _tier1_circuit_open = True
    _tier1_circuit_opened_at = time.time()


def _record_tier1_success():
    global _tier1_circuit_open
    _tier1_circuit_open = False


def compute_chennai_traffic_multiplier(city_id: str, travel_date: Optional[str] = None) -> float:
    """
    Evaluates dynamic peak-hour traffic multipliers for Chennai.
    Applied at read time; never stored in cache.
    """
    if not city_id or city_id.lower() != "chennai":
        return 1.0

    now = datetime.now()
    cur_hour = now.hour + now.minute / 60.0

    # Morning rush: 08:30 - 10:30
    if 8.5 <= cur_hour <= 10.5:
        return 1.25
    # Evening rush: 17:30 - 20:00
    if 17.5 <= cur_hour <= 20.0:
        return 1.35

    return 1.0


class RoutingService:
    def __init__(self):
        self.local_driving_url = settings.OSRM_LOCAL_DRIVING_URL.rstrip("/")
        self.local_walking_url = settings.OSRM_LOCAL_WALKING_URL.rstrip("/")
        self.public_demo_url = settings.OSRM_PUBLIC_DEMO_URL.rstrip("/")
        self.timeout_seconds = settings.OSRM_TIMEOUT_SECONDS

    def _format_step_instruction(self, step: Dict[str, Any]) -> str:
        maneuver = step.get("maneuver", {})
        m_type = maneuver.get("type", "turn")
        modifier = maneuver.get("modifier", "")
        name = step.get("name", "")
        
        if m_type == "depart":
            instruction = f"Depart on {name}" if name else "Depart toward destination"
        elif m_type == "arrive":
            instruction = "Arrive at destination"
        elif modifier:
            instruction = f"Turn {modifier} onto {name}" if name else f"Turn {modifier}"
        else:
            instruction = f"Continue on {name}" if name else "Continue straight"
        return instruction

    def get_route(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        mode: RouteModeEnum = "driving",
        city_id: str = "pondicherry",
        traffic_multiplier: float = 1.0,
        travel_date: Optional[str] = None
    ) -> RouteResponse:
        """
        Calculates a turn-by-turn route between two coordinates using:
        1. MongoDB route cache lookup (with quality upgrade soft-misses & anti-loop retry limit)
        2. Single-flight request coalescing for identical concurrent cache misses
        3. 3-tier cascade: Local OSRM -> Public Demo (throttled) -> Haversine Detour
        4. Read-time Chennai peak traffic scaling & festival road closure intersection check
        """
        # Edge case: Identical origin and destination
        if abs(origin_lat - dest_lat) < 1e-6 and abs(origin_lng - dest_lng) < 1e-6:
            return RouteResponse(
                origin=Coordinates(lat=origin_lat, lng=origin_lng),
                destination=Coordinates(lat=dest_lat, lng=dest_lng),
                mode=mode,
                distance_km=0.0,
                estimated_travel_time_minutes=0.0,
                tier_used=RoutingTier.local_osrm,
                walking_source=WalkingSource.local_foot if mode == "walking" else None,
                is_approximate=False,
                approximate_label="",
                polyline_geojson={
                    "type": "LineString",
                    "coordinates": [[origin_lng, origin_lat], [dest_lng, dest_lat]]
                },
                turn_by_turn_steps=[
                    TurnStep(
                        instruction="You are already at your destination",
                        distance_meters=0.0,
                        duration_seconds=0.0,
                        street_name=""
                    )
                ]
            )

        # ----------------------------------------------------------------------
        # 1. CACHE LOOKUP (Read raw values, apply read-time scaling)
        # ----------------------------------------------------------------------
        tier1_up = _is_tier1_healthy()
        cached = route_cache_service.get_cached_route(
            o_lat=origin_lat,
            o_lng=origin_lng,
            d_lat=dest_lat,
            d_lng=dest_lng,
            mode=mode,
            fossgis_foot_healthy=True,
            tier1_healthy=tier1_up
        )

        if cached is not None:
            raw_dur = cached.get("raw_duration_min", cached.get("duration_min", 0.0))
            dist_km = cached.get("distance_km", 0.0)
            cached_tier_str = cached.get("tier_used", RoutingTier.public_demo.value)
            try:
                tier_used = RoutingTier(cached_tier_str)
            except ValueError:
                tier_used = RoutingTier.public_demo

            ws_str = cached.get("walking_source")
            walking_source = WalkingSource(ws_str) if ws_str else None

            # Dynamic is_approximate evaluation: True if tier != local_osrm
            is_approximate = (tier_used != RoutingTier.local_osrm)
            approx_label = "(Approximate travel time)" if is_approximate else ""

            # Apply read-time Chennai traffic multiplier
            traffic_mult = compute_chennai_traffic_multiplier(city_id, travel_date)
            total_multiplier = traffic_multiplier * traffic_mult if mode == "driving" else 1.0
            final_duration = round(raw_dur * total_multiplier, 1)

            # Reconstruct turn steps
            steps = []
            for s in cached.get("turn_by_turn_steps", []):
                steps.append(TurnStep(**s) if isinstance(s, dict) else s)

            geojson = cached.get("polyline_geojson", {
                "type": "LineString",
                "coordinates": [[origin_lng, origin_lat], [dest_lng, dest_lat]]
            })

            # Read-time festival road closure intersection check
            closure_aff, closure_warn, closure_evs = route_cache_service.check_festival_closures(
                geojson.get("coordinates", []),
                city_id=city_id,
                travel_date=travel_date
            )

            return RouteResponse(
                origin=Coordinates(lat=origin_lat, lng=origin_lng),
                destination=Coordinates(lat=dest_lat, lng=dest_lng),
                mode=mode,
                distance_km=dist_km,
                estimated_travel_time_minutes=final_duration,
                tier_used=tier_used,
                walking_source=walking_source,
                is_approximate=is_approximate,
                approximate_label=approx_label,
                polyline_geojson=geojson,
                turn_by_turn_steps=steps,
                closure_affected=closure_aff,
                closure_warning=closure_warn,
                closure_events=closure_evs
            )

        # ----------------------------------------------------------------------
        # 2. CACHE MISS: Single-Flight Coalesced Cascade Execution
        # ----------------------------------------------------------------------
        flight_key = route_cache_service.format_route_key(origin_lat, origin_lng, dest_lat, dest_lng, mode)
        return route_cache_service.single_flight.execute(
            flight_key,
            self._compute_and_cache_route,
            origin_lat, origin_lng, dest_lat, dest_lng, mode, city_id, traffic_multiplier, travel_date
        )

    def _compute_and_cache_route(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        mode: RouteModeEnum,
        city_id: str,
        traffic_multiplier: float,
        travel_date: Optional[str]
    ) -> RouteResponse:
        """Internal uncached route cascade execution."""
        raw_dist_km: float = 0.0
        raw_dur_min: float = 0.0
        tier_used: RoutingTier = RoutingTier.haversine_detour
        walking_source: Optional[WalkingSource] = None
        polyline_geojson: Dict[str, Any] = {}
        steps: List[TurnStep] = []

        # ----------------------------------------------------------------------
        # TIER 1: Local OSRM
        # ----------------------------------------------------------------------
        if _is_tier1_healthy():
            base_local = self.local_walking_url if mode == "walking" else self.local_driving_url
            local_url = f"{base_local}/route/v1/{mode}/{origin_lng},{origin_lat};{dest_lng},{dest_lat}?overview=full&geometries=geojson&steps=true"
            try:
                req = urllib.request.Request(local_url, headers={"User-Agent": OSRM_USER_AGENT})
                with urllib.request.urlopen(req, timeout=0.8) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        if data.get("code") == "Ok" and data.get("routes"):
                            _record_tier1_success()
                            route = data["routes"][0]
                            dist_m = float(route.get("distance", 0.0))
                            dur_s = float(route.get("duration", 0.0))
                            raw_dist_km = round(dist_m / 1000.0, 3)
                            raw_dur_min = round(dur_s / 60.0, 1)
                            tier_used = RoutingTier.local_osrm
                            walking_source = WalkingSource.local_foot if mode == "walking" else None

                            for leg in route.get("legs", []):
                                for s in leg.get("steps", []):
                                    steps.append(TurnStep(
                                        instruction=self._format_step_instruction(s),
                                        distance_meters=float(s.get("distance", 0.0)),
                                        duration_seconds=float(s.get("duration", 0.0)),
                                        street_name=s.get("name", "")
                                    ))
                            polyline_geojson = route.get("geometry", {})
            except Exception as e:
                _record_tier1_failure()
                logger.debug(f"[RoutingService] Tier 1 (local_osrm) unavailable: {e}. Circuit opened for 45s.")

        # ----------------------------------------------------------------------
        # TIER 2: Public OSRM Demo / FOSSGIS Foot (with 1 req/s Throttle & Max-Wait)
        # ----------------------------------------------------------------------
        if tier_used == RoutingTier.haversine_detour:
            try:
                _acquire_tier2_slot()

                if mode == "walking":
                    primary_url = f"{OSRM_FOSSGIS_FOOT_URL}/route/v1/driving/{origin_lng},{origin_lat};{dest_lng},{dest_lat}?overview=full&geometries=geojson&steps=true"
                else:
                    primary_url = f"{self.public_demo_url}/route/v1/{mode}/{origin_lng},{origin_lat};{dest_lng},{dest_lat}?overview=full&geometries=geojson&steps=true"

                req = urllib.request.Request(primary_url, headers={"User-Agent": OSRM_USER_AGENT})
                with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        if data.get("code") == "Ok" and data.get("routes"):
                            route = data["routes"][0]
                            dist_m = float(route.get("distance", 0.0))
                            raw_dist_km = round(dist_m / 1000.0, 3)
                            dur_s = float(route.get("duration", 0.0))

                            if mode == "walking":
                                # Verification check: If duration implies > 15 km/h, correct via 1.25 m/s
                                implied_speed_kmh = (dist_m / 1000.0) / (dur_s / 3600.0) if dur_s > 0 else 0.0
                                if implied_speed_kmh > 12.0:
                                    dur_s = dist_m / PEDESTRIAN_SPEED_MS
                                    walking_source = WalkingSource.corrected_car
                                else:
                                    walking_source = WalkingSource.fossgis_foot
                            else:
                                walking_source = None

                            raw_dur_min = round(dur_s / 60.0, 1)
                            tier_used = RoutingTier.public_demo

                            for leg in route.get("legs", []):
                                for s in leg.get("steps", []):
                                    steps.append(TurnStep(
                                        instruction=self._format_step_instruction(s),
                                        distance_meters=float(s.get("distance", 0.0)),
                                        duration_seconds=float(s.get("duration", 0.0)),
                                        street_name=s.get("name", "")
                                    ))
                            polyline_geojson = route.get("geometry", {})
            except Tier2ThrottleExceeded as te:
                logger.info(f"[RoutingService] Tier 2 throttle queue exceeded ({te}). Cascading to Tier 3.")
            except Exception as e:
                logger.warning(f"[RoutingService] Tier 2 unavailable: {e}. Cascading to Tier 3.")

        # ----------------------------------------------------------------------
        # TIER 3: Deterministic Haversine Detour
        # ----------------------------------------------------------------------
        if tier_used == RoutingTier.haversine_detour:
            raw_dist_km = round(estimate_road_distance_km(
                origin_lat, origin_lng, dest_lat, dest_lng, city_id=city_id
            ), 3)
            raw_dur_min = estimate_travel_time_minutes(raw_dist_km, mode=mode)
            tier_used = RoutingTier.haversine_detour
            walking_source = WalkingSource.corrected_car if mode == "walking" else None

            detour = get_detour_factor(city_id)
            speed_kmh = DEFAULT_WALKING_SPEED_KMH if mode == "walking" else DEFAULT_DRIVING_SPEED_KMH
            steps = [
                TurnStep(
                    instruction=f"Follow route toward destination (straight-line with {detour:.2f}x detour)",
                    distance_meters=round(raw_dist_km * 1000.0, 1),
                    duration_seconds=round(raw_dur_min * 60.0, 1),
                    street_name=f"Direct Corridor ({speed_kmh} km/h)"
                )
            ]
            polyline_geojson = {
                "type": "LineString",
                "coordinates": [
                    [origin_lng, origin_lat],
                    [round((origin_lng + dest_lng) / 2.0, 6), round((origin_lat + dest_lat) / 2.0, 6)],
                    [dest_lng, dest_lat]
                ]
            }

        # ----------------------------------------------------------------------
        # PERSISTENCE: Save to MongoDB cache (Tier 3 is automatically skipped)
        # ----------------------------------------------------------------------
        if tier_used != RoutingTier.haversine_detour:
            route_cache_service.save_route(
                o_lat=origin_lat,
                o_lng=origin_lng,
                d_lat=dest_lat,
                d_lng=dest_lng,
                mode=mode,
                distance_km=raw_dist_km,
                raw_duration_min=raw_dur_min,
                tier_used=tier_used,
                walking_source=walking_source,
                polyline_geojson=polyline_geojson,
                steps=steps
            )

        # ----------------------------------------------------------------------
        # READ-TIME ENRICHMENT: Chennai Traffic Scaling & Festival Closures
        # ----------------------------------------------------------------------
        traffic_mult = compute_chennai_traffic_multiplier(city_id, travel_date)
        total_multiplier = traffic_multiplier * traffic_mult if mode == "driving" else 1.0
        final_dur_min = round(raw_dur_min * total_multiplier, 1)

        is_approximate = (tier_used != RoutingTier.local_osrm)
        approx_label = "(Approximate travel time)" if is_approximate else ""

        closure_aff, closure_warn, closure_evs = route_cache_service.check_festival_closures(
            polyline_geojson.get("coordinates", []),
            city_id=city_id,
            travel_date=travel_date
        )

        return RouteResponse(
            origin=Coordinates(lat=origin_lat, lng=origin_lng),
            destination=Coordinates(lat=dest_lat, lng=dest_lng),
            mode=mode,
            distance_km=raw_dist_km,
            estimated_travel_time_minutes=final_dur_min,
            tier_used=tier_used,
            walking_source=walking_source,
            is_approximate=is_approximate,
            approximate_label=approx_label,
            polyline_geojson=polyline_geojson,
            turn_by_turn_steps=steps,
            warning="Offline straight-line route approximation with empirical detour factor" if tier_used == RoutingTier.haversine_detour else None,
            closure_affected=closure_aff,
            closure_warning=closure_warn,
            closure_events=closure_evs
        )

    def get_matrix(
        self,
        coordinates: List[Coordinates],
        mode: RouteModeEnum = "driving",
        city_id: str = "pondicherry"
    ) -> RouteMatrixResponse:
        """
        Computes NxN travel distance and duration matrix.
        1. Checks MongoDB cell cache for existing directed pairs.
        2. If missing pairs exist, dispatches ONE single batch /table call (1 throttle slot).
        3. Persists computed cells (excluding Tier 3).
        4. Returns mixed-tier summary, cell tiers, and is_approximate label.
        """
        n = len(coordinates)
        if n < 2:
            return RouteMatrixResponse(
                durations_minutes=[[0.0]],
                distances_km=[[0.0]],
                tier_summary={RoutingTier.local_osrm.value: 1},
                is_mixed_tier=False,
                is_approximate=False,
                tier_used=RoutingTier.local_osrm
            )

        # 1. Prepare key lookup
        pair_to_key: Dict[Tuple[int, int], str] = {}
        all_keys: List[str] = []
        for i in range(n):
            for j in range(n):
                if i != j:
                    k = route_cache_service.format_cell_key(
                        coordinates[i].lat, coordinates[i].lng,
                        coordinates[j].lat, coordinates[j].lng,
                        mode
                    )
                    pair_to_key[(i, j)] = k
                    all_keys.append(k)

        # 2. Batch lookup cached cells
        cached_cells = route_cache_service.get_cached_cells(all_keys)

        # Identify missing non-diagonal pairs
        missing_pairs = [p for p in pair_to_key if pair_to_key[p] not in cached_cells]

        fresh_cells_map: Dict[Tuple[int, int], Dict[str, Any]] = {}

        if missing_pairs:
            # 3. Issue ONE single batch /table call with annotations=duration,distance
            coord_str = ";".join(f"{c.lng},{c.lat}" for c in coordinates)
            table_success = False

            # TIER 1: Local Table
            if _is_tier1_healthy():
                base_local = self.local_walking_url if mode == "walking" else self.local_driving_url
                local_url = f"{base_local}/table/v1/{mode}/{coord_str}?annotations=duration,distance"
                try:
                    req = urllib.request.Request(local_url, headers={"User-Agent": OSRM_USER_AGENT})
                    with urllib.request.urlopen(req, timeout=1.0) as resp:
                        if resp.status == 200:
                            data = json.loads(resp.read().decode("utf-8"))
                            if data.get("code") == "Ok":
                                _record_tier1_success()
                                table_success = True
                                raw_durs = data.get("durations", [])
                                raw_dists = data.get("distances", [])
                                for i in range(n):
                                    for j in range(n):
                                        if i != j:
                                            dur_m = round(float(raw_durs[i][j]) / 60.0, 1)
                                            dist_k = round(float(raw_dists[i][j]) / 1000.0, 3)
                                            fresh_cells_map[(i, j)] = {
                                                "cache_key": pair_to_key[(i, j)],
                                                "origin_lat": coordinates[i].lat,
                                                "origin_lng": coordinates[i].lng,
                                                "dest_lat": coordinates[j].lat,
                                                "dest_lng": coordinates[j].lng,
                                                "mode": mode,
                                                "distance_km": dist_k,
                                                "duration_min": dur_m,
                                                "tier_used": RoutingTier.local_osrm,
                                                "walking_source": WalkingSource.local_foot if mode == "walking" else None
                                            }
                except Exception as e:
                    _record_tier1_failure()
                    logger.debug(f"[RoutingService] Matrix Tier 1 unavailable: {e}")

            # TIER 2: Public OSRM / FOSSGIS Foot Demo Table
            if not table_success:
                try:
                    _acquire_tier2_slot()
                    if mode == "walking":
                        public_url = f"{OSRM_FOSSGIS_FOOT_URL}/table/v1/driving/{coord_str}?annotations=duration,distance"
                    else:
                        public_url = f"{self.public_demo_url}/table/v1/{mode}/{coord_str}?annotations=duration,distance"

                    req = urllib.request.Request(public_url, headers={"User-Agent": OSRM_USER_AGENT})
                    with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                        if resp.status == 200:
                            data = json.loads(resp.read().decode("utf-8"))
                            if data.get("code") == "Ok":
                                table_success = True
                                raw_durs = data.get("durations", [])
                                raw_dists = data.get("distances", [])
                                for i in range(n):
                                    for j in range(n):
                                        if i != j:
                                            dist_m = float(raw_dists[i][j])
                                            dur_s = float(raw_durs[i][j])
                                            ws = None
                                            if mode == "walking":
                                                implied_spd = (dist_m / 1000.0) / (dur_s / 3600.0) if dur_s > 0 else 0.0
                                                if implied_spd > 12.0:
                                                    dur_s = dist_m / PEDESTRIAN_SPEED_MS
                                                    ws = WalkingSource.corrected_car
                                                else:
                                                    ws = WalkingSource.fossgis_foot

                                            dist_k = round(dist_m / 1000.0, 3)
                                            dur_m = round(dur_s / 60.0, 1)
                                            fresh_cells_map[(i, j)] = {
                                                "cache_key": pair_to_key[(i, j)],
                                                "origin_lat": coordinates[i].lat,
                                                "origin_lng": coordinates[i].lng,
                                                "dest_lat": coordinates[j].lat,
                                                "dest_lng": coordinates[j].lng,
                                                "mode": mode,
                                                "distance_km": dist_k,
                                                "duration_min": dur_m,
                                                "tier_used": RoutingTier.public_demo,
                                                "walking_source": ws
                                            }
                except Exception as e:
                    logger.warning(f"[RoutingService] Matrix Tier 2 unavailable: {e}")

            # TIER 3 Fallback for missing pairs
            if not table_success:
                for (i, j) in missing_pairs:
                    d_km = round(estimate_road_distance_km(
                        coordinates[i].lat, coordinates[i].lng,
                        coordinates[j].lat, coordinates[j].lng,
                        city_id=city_id
                    ), 3)
                    t_min = estimate_travel_time_minutes(d_km, mode=mode)
                    fresh_cells_map[(i, j)] = {
                        "cache_key": pair_to_key[(i, j)],
                        "origin_lat": coordinates[i].lat,
                        "origin_lng": coordinates[i].lng,
                        "dest_lat": coordinates[j].lat,
                        "dest_lng": coordinates[j].lng,
                        "mode": mode,
                        "distance_km": d_km,
                        "duration_min": t_min,
                        "tier_used": RoutingTier.haversine_detour,
                        "walking_source": WalkingSource.corrected_car if mode == "walking" else None
                    }

            # Persist newly computed cells into MongoDB (Tier 3 cells will be filtered out)
            cells_to_save = [
                fresh_cells_map[p] for p in fresh_cells_map
                if fresh_cells_map[p]["tier_used"] != RoutingTier.haversine_detour
            ]
            if cells_to_save:
                route_cache_service.save_matrix_cells(cells_to_save)

        # 4. Assemble complete NxN matrix & collect tier metadata
        durations: List[List[float]] = []
        distances: List[List[float]] = []
        cell_tiers: List[List[RoutingTier]] = []
        tier_counts: Dict[str, int] = {
            RoutingTier.local_osrm.value: 0,
            RoutingTier.public_demo.value: 0,
            RoutingTier.haversine_detour.value: 0
        }

        for i in range(n):
            dur_row: List[float] = []
            dist_row: List[float] = []
            tier_row: List[RoutingTier] = []
            for j in range(n):
                if i == j:
                    dur_row.append(0.0)
                    dist_row.append(0.0)
                    tier_row.append(RoutingTier.local_osrm)
                    tier_counts[RoutingTier.local_osrm.value] += 1
                else:
                    k = pair_to_key[(i, j)]
                    if k in cached_cells:
                        c_doc = cached_cells[k]
                        d_val = c_doc.get("duration_min", 0.0)
                        dist_val = c_doc.get("distance_km", 0.0)
                        t_str = c_doc.get("tier_used", RoutingTier.public_demo.value)
                        try:
                            t_enum = RoutingTier(t_str)
                        except ValueError:
                            t_enum = RoutingTier.public_demo
                    else:
                        f_doc = fresh_cells_map[(i, j)]
                        d_val = f_doc["duration_min"]
                        dist_val = f_doc["distance_km"]
                        t_enum = f_doc["tier_used"]

                    dur_row.append(d_val)
                    dist_row.append(dist_val)
                    tier_row.append(t_enum)
                    tier_counts[t_enum.value] += 1

            durations.append(dur_row)
            distances.append(dist_row)
            cell_tiers.append(tier_row)

        # Evaluate matrix summary
        active_tiers = {k: v for k, v in tier_counts.items() if v > 0}
        is_mixed = len(active_tiers) > 1
        is_approx = any(k != RoutingTier.local_osrm.value and v > 0 for k, v in tier_counts.items())

        # Determine dominant tier for top-level backward compatibility
        dominant_tier = RoutingTier.local_osrm
        if tier_counts[RoutingTier.haversine_detour.value] > 0:
            dominant_tier = RoutingTier.haversine_detour
        elif tier_counts[RoutingTier.public_demo.value] > 0:
            dominant_tier = RoutingTier.public_demo

        return RouteMatrixResponse(
            durations_minutes=durations,
            distances_km=distances,
            cell_tiers=cell_tiers,
            tier_summary=tier_counts,
            is_mixed_tier=is_mixed,
            is_approximate=is_approx,
            approximate_label="(Approximate travel time)" if is_approx else "",
            tier_used=dominant_tier,
            walking_source=WalkingSource.fossgis_foot if mode == "walking" else None
        )


routing_service = RoutingService()
