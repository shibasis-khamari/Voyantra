import math
import time
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from pymongo import MongoClient

KOLKATA_TZ = ZoneInfo("Asia/Kolkata")

from .festivals_service import festivals_service
from .places_service import places_service
from .weather_service import weather_service
from ..core.database import MONGODB_URL, DB_NAME
from ..core.geo import haversine_km
from ..schemas.crowd import (
    CrowdReportLevel,
    CrowdReportRequest,
    CrowdReportResponse,
    LiveCrowdResponse,
    CROWD_LEVEL_TO_DENSITY
)

logger = logging.getLogger(__name__)

REPORTS_COLLECTION = "crowd_reports"
SNAPSHOTS_COLLECTION = "feature_snapshots"
REPORTS_TTL_SECONDS = 86400  # 24 hours
GEOFENCE_RADIUS_METERS = 200.0
REPORT_COOLDOWN_SECONDS = 900.0  # 15 minutes
HALF_LIFE_MINUTES = 30.0


class CrowdService:
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db = None
        self._init_db()
        self.seasonality_data = self._load_seasonality_index()

    def _load_seasonality_index(self) -> Dict[str, Any]:
        """Loads data-calibrated empirical seasonality factors from JSON."""
        path = Path(__file__).resolve().parent.parent / "data" / "seasonality_index.json"
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"[CrowdService] Error loading seasonality index: {e}")
        return {}

    def get_seasonality_info(self, city_id: str, month: int) -> Dict[str, Any]:
        """
        Phase 6: Returns empirical seasonality data for a given city and month.
        - Chennai: calibrated to Tamil Nadu Tourism Dept 2022-2024 District 3302 records.
        - Pondicherry: Ministry of Tourism 2014 survey prior.
        """
        cid = "chennai" if "chennai" in city_id.lower() else "pondicherry"
        cities = self.seasonality_data.get("cities", {})
        city_rec = cities.get(cid, {})
        month_rec = city_rec.get("months", {}).get(str(month), {})
        prov_label = city_rec.get("provenance_label", "2014 survey data, rough prior" if cid == "pondicherry" else "Tamil Nadu Tourism Dept (2022–2024 District 3302 Records)")

        return {
            "city_id": cid,
            "month": month,
            "month_name": month_rec.get("name", ""),
            "multiplier": month_rec.get("multiplier", 1.0),
            "seasonal_point_adjustment": month_rec.get("seasonal_point_adjustment", 0),
            "season_category": month_rec.get("season_category", "Moderate"),
            "drivers": month_rec.get("drivers", "Standard tourist season"),
            "provenance_label": prov_label
        }

    def _init_db(self):
        try:
            self.client = MongoClient(
                MONGODB_URL,
                serverSelectionTimeoutMS=500,
                connectTimeoutMS=500,
                socketTimeoutMS=500
            )
            self.db = self.client[DB_NAME]
            self.ensure_indexes()
        except Exception as e:
            logger.warning(f"[CrowdService] MongoDB notice ({e}). Operating resiliently.")

    def ensure_indexes(self):
        """Idempotent index setup for crowd_reports and feature_snapshots."""
        if self.db is None:
            return
        try:
            # 1. crowd_reports: TTL on created_at (24h) + compound index for fast decay aggregation
            rep_col = self.db[REPORTS_COLLECTION]
            rep_col.create_index("created_at", expireAfterSeconds=REPORTS_TTL_SECONDS)
            rep_col.create_index([("place_id", 1), ("created_at", -1)])
            rep_col.create_index([("reporter_hash", 1), ("place_id", 1), ("created_at", -1)])

            # 2. feature_snapshots: compound index for model evaluation
            snap_col = self.db[SNAPSHOTS_COLLECTION]
            snap_col.create_index([("place_id", 1), ("created_at", -1)])
            snap_col.create_index("is_simulated")
        except Exception as e:
            logger.warning(f"[CrowdService] ensure_indexes notice: {e}")

    # -------------------------------------------------------------------------
    # Rule-Based Baseline Engine (Phase 3 Core)
    # -------------------------------------------------------------------------
    def estimate_place_crowd(
        self,
        city_id: str,
        place_id: str,
        target_date_str: Optional[str] = None,
        hour: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        place = places_service.get_place_by_id(place_id, city_id)
        if not place:
            other_city = "chennai" if city_id.lower() == "pondicherry" else "pondicherry"
            place = places_service.get_place_by_id(place_id, other_city)
            if place:
                city_id = other_city
            else:
                return None

        if target_date_str:
            try:
                dt = datetime.strptime(target_date_str, "%Y-%m-%d").replace(tzinfo=KOLKATA_TZ)
            except ValueError:
                dt = datetime.now(KOLKATA_TZ)
        else:
            dt = datetime.now(KOLKATA_TZ)

        current_hour = hour if hour is not None else dt.hour
        day_of_week = dt.weekday()  # 0=Mon, 5=Sat, 6=Sun
        month = dt.month

        category = place.category.value.lower()
        place_name = place.name

        base_tendency = place.crowd_tendency.value.lower()
        base_score = 30 if base_tendency == "low" else 55 if base_tendency == "medium" else 75

        drivers = []

        # 1. TIME OF DAY RULE
        time_factor = 0
        if category == "beach":
            if 17 <= current_hour <= 19:
                time_factor = 30
                drivers.append("Sunset Peak (5:00 PM - 7:30 PM)")
            elif 6 <= current_hour <= 8:
                time_factor = 15
                drivers.append("Sunrise Walkers (6:00 AM - 8:00 AM)")
            elif current_hour >= 21 or current_hour < 5:
                time_factor = -25
                drivers.append("Off-peak late night")
            else:
                time_factor = 5

        elif category in ["spiritual", "temple"]:
            if 6 <= current_hour <= 9:
                time_factor = 25
                drivers.append("Morning Worship & Aarti (6:00 AM - 9:00 AM)")
            elif 17 <= current_hour <= 20:
                time_factor = 25
                drivers.append("Evening Pooja Hours (5:00 PM - 8:00 PM)")
            elif 12 <= current_hour <= 16:
                time_factor = -20
                drivers.append("Mid-day Temple Sanctum Closure")
            else:
                time_factor = 0

        elif category in ["cafe", "dining", "restaurant"]:
            if 12 <= current_hour <= 15:
                time_factor = 25
                drivers.append("Lunch Rush (12:00 PM - 3:00 PM)")
            elif 19 <= current_hour <= 22:
                time_factor = 30
                drivers.append("Dinner Peak (7:00 PM - 10:00 PM)")
            else:
                time_factor = -10

        elif category == "heritage":
            if 10 <= current_hour <= 16:
                time_factor = 20
                drivers.append("Daytime Sightseeing (10:00 AM - 4:00 PM)")
            else:
                time_factor = -15
        else:
            time_factor = 10 if 10 <= current_hour <= 18 else -10

        # 2. WEEKEND RULE
        day_factor = 0
        if day_of_week in [5, 6]:
            day_factor = 20
            drivers.append("Weekend Outstation Inflow (+20%)")
        elif day_of_week == 4:
            day_factor = 10
            drivers.append("Friday Evening Inflow (+10%)")
        else:
            day_factor = -5

        # 3. EMPIRICAL SEASONALITY RULE (Phase 6 Data-Calibrated)
        season_info = self.get_seasonality_info(city_id, month)
        season_factor = season_info["seasonal_point_adjustment"]
        multiplier = season_info["multiplier"]
        cat_name = season_info["season_category"]
        driver_desc = season_info["drivers"]
        prov_label = season_info["provenance_label"]

        sign = f"+{season_factor}" if season_factor >= 0 else str(season_factor)
        drivers.append(f"Seasonality ({cat_name}, {multiplier}x): {driver_desc} [{sign}%]")

        # 4. FESTIVAL CALENDAR RULE
        fest_factor = 0
        active_fests = festivals_service.get_active_festivals_for_date(city_id, dt.strftime("%Y-%m-%d"))
        fest_alert = None
        if active_fests:
            fest_names = [f["name"] for f in active_fests]
            fest_factor = 25
            fest_alert = f"Active Festival: {', '.join(fest_names)} (+25% surge)"
            drivers.append(fest_alert)

        density = int(min(100, max(5, base_score + time_factor + day_factor + season_factor + fest_factor)))

        if density >= 80:
            crowd_level = "peak"
            status_badge = "🟣 Overcrowded / Peak Surge"
        elif density >= 60:
            crowd_level = "high"
            status_badge = "🔴 Bustling / High Crowd"
        elif density >= 40:
            crowd_level = "medium"
            status_badge = "🟡 Moderate Activity"
        else:
            crowd_level = "low"
            status_badge = "🟢 Serene / Low Crowd"

        hourly_curve = self._compute_hourly_curve(category, base_score, day_factor, season_factor, fest_factor)
        quiet_window = self._determine_quiet_window(category, hourly_curve)

        return {
            "place_id": place.id,
            "place_name": place.name,
            "category": category,
            "city_id": city_id,
            "target_date": dt.strftime("%Y-%m-%d"),
            "hour": current_hour,
            "crowd_level": crowd_level,
            "crowd_density_pct": density,
            "status_badge": status_badge,
            "drivers": drivers,
            "hourly_curve": hourly_curve,
            "quiet_window": quiet_window,
            "festival_alert": fest_alert,
            "seasonality": season_info
        }

    def _compute_hourly_curve(self, category: str, base: int, day_f: int, season_f: int, fest_f: int) -> List[Dict[str, Any]]:
        curve = []
        for h in range(6, 23):
            if category == "beach":
                mult = 0.3 if h < 15 else (0.9 if 17 <= h <= 19 else 0.5)
            elif category in ["spiritual", "temple"]:
                mult = 0.8 if (6 <= h <= 9 or 17 <= h <= 20) else (0.2 if 12 <= h <= 15 else 0.4)
            elif category in ["cafe", "dining"]:
                mult = 0.85 if (16 <= h <= 21) else (0.7 if 12 <= h <= 14 else 0.2)
            else:
                mult = 0.8 if (10 <= h <= 16) else 0.3

            score = int(min(100, max(12, (base + day_f + season_f + fest_f) * mult + (h % 3 * 2))))
            time_str = f"{h if h <= 12 else h - 12}:00 {'AM' if h < 12 else 'PM'}"
            curve.append({"hour": h, "time_label": time_str, "density_pct": score})
        return curve

    def _determine_quiet_window(self, category: str, curve: List[Dict[str, Any]]) -> str:
        sorted_hours = sorted(curve, key=lambda x: x["density_pct"])
        if sorted_hours:
            best = sorted_hours[0]
            second = sorted_hours[1] if len(sorted_hours) > 1 else best
            return f"{best['time_label']} - {second['time_label']} (Lowest Crowd)"
        return "Early Morning (7:00 AM - 9:30 AM)"

    def get_city_crowd_index(self, city_id: str, target_date_str: Optional[str] = None) -> Dict[str, Any]:
        cid = city_id.lower()
        active_fests = festivals_service.get_active_festivals_for_date(cid, target_date_str)
        all_places = places_service.get_all_places(cid)

        sample_places = all_places[:8] if all_places else []
        densities = []
        for p in sample_places:
            est = self.estimate_place_crowd(cid, p.id, target_date_str)
            if est:
                densities.append(est["crowd_density_pct"])

        avg_density = int(sum(densities) / len(densities)) if densities else 45
        level = "peak" if active_fests or avg_density >= 75 else "high" if avg_density >= 60 else "medium" if avg_density >= 40 else "low"

        return {
            "city_id": cid,
            "overall_crowd_level": level,
            "avg_crowd_density_pct": avg_density,
            "active_festivals_count": len(active_fests),
            "active_festivals": active_fests,
            "advisory_summary": f"{len(active_fests)} Active Local Festival Advisories" if active_fests else "Normal Traffic & Tourist Conditions"
        }

    # -------------------------------------------------------------------------
    # Phase 5: Crowdsourced Real-Time Reporting & Snapshot Logging
    # -------------------------------------------------------------------------
    def submit_crowd_report(
        self,
        request: CrowdReportRequest,
        client_ip: str,
        user_id: Optional[str] = None,
        is_simulated: bool = False
    ) -> CrowdReportResponse:
        """
        Processes 1-tap live crowd submission with geofence guard (<= 200m),
        15-minute cooldown, snapshot logging (preventing rule leakage),
        and real-time exponential decay blending.
        """
        city_id = request.city_id.lower().strip()
        place = places_service.get_place_by_id(request.place_id, city_id)
        if not place:
            # Check fallback city
            other_city = "chennai" if city_id == "pondicherry" else "pondicherry"
            place = places_service.get_place_by_id(request.place_id, other_city)
            if place:
                city_id = other_city
            else:
                raise ValueError(f"Place with id '{request.place_id}' not found.")

        # 1. Geofence Guard (<= 200m Haversine)
        p_lat = place.coordinates.lat
        p_lng = place.coordinates.lng
        dist_km = haversine_km(request.user_lat, request.user_lng, p_lat, p_lng)
        dist_m = dist_km * 1000.0

        if dist_m > GEOFENCE_RADIUS_METERS:
            raise PermissionError(
                f"Geofence verification failed. You are {dist_m:.1f}m away from {place.name}. "
                f"Live crowd reporting requires being on-site (within {int(GEOFENCE_RADIUS_METERS)}m)."
            )

        # 2. Rate Limiting & Anonymized Reporter Hash
        salt = "VOYANTRA_PRIVACY_SALT_2026"
        identifier = user_id or client_ip or "anonymous"
        reporter_hash = hashlib.sha256(f"{identifier}:{salt}".encode()).hexdigest()[:16]

        now_utc = datetime.now(timezone.utc)
        now_ist = datetime.now(KOLKATA_TZ)

        if self.db is not None:
            # Check 15-minute cooldown (applies to all public submissions)
            if not is_simulated:
                cutoff = now_utc - timedelta(seconds=REPORT_COOLDOWN_SECONDS)
                recent_rep = self.db[REPORTS_COLLECTION].find_one({
                    "reporter_hash": reporter_hash,
                    "place_id": request.place_id,
                    "created_at": {"$gte": cutoff}
                })
                if recent_rep:
                    created_dt = recent_rep["created_at"]
                    if created_dt.tzinfo is None:
                        created_dt = created_dt.replace(tzinfo=timezone.utc)
                    elapsed_s = (now_utc - created_dt).total_seconds()
                    rem_min = int(max(1, (REPORT_COOLDOWN_SECONDS - elapsed_s) // 60))
                    raise TimeoutError(
                        f"Cooldown active. You submitted a report {int(elapsed_s // 60)}m ago. "
                        f"Next submission permitted in {rem_min} min."
                    )

        reported_density = CROWD_LEVEL_TO_DENSITY.get(request.crowd_level, 50)

        # 3. Store Report in MongoDB (TTL: 24h)
        report_doc = {
            "place_id": request.place_id,
            "city_id": city_id,
            "crowd_level": request.crowd_level.value,
            "reported_density_pct": reported_density,
            "reporter_hash": reporter_hash,
            "is_simulated": is_simulated,
            "verification_distance_m": round(dist_m, 1),
            "created_at": now_utc
        }

        if self.db is not None:
            try:
                self.db[REPORTS_COLLECTION].insert_one(report_doc)
            except Exception as e:
                logger.warning(f"[CrowdService] Failed to insert crowd report: {e}")

        # 4. Feature Snapshot Logging (Excludes Rule as an ML Input Feature)
        rule_est = self.estimate_place_crowd(city_id, request.place_id, target_date_str=now_ist.strftime("%Y-%m-%d"), hour=now_ist.hour)
        rule_baseline_pct = rule_est["crowd_density_pct"] if rule_est else 50

        # Query Open-Meteo weather
        weather = weather_service.get_current_weather(city_id)
        active_fests = festivals_service.get_active_festivals_for_date(city_id, now_ist.strftime("%Y-%m-%d"))

        snapshot_doc = {
            "place_id": request.place_id,
            "city_id": city_id,
            "category": place.category.value.lower(),
            "reported_density_pct": reported_density,
            # CRITICAL RULE: rule_baseline_density_pct is STRICTLY logged for evaluation baseline, NOT as training feature
            "rule_baseline_density_pct": rule_baseline_pct,
            "is_simulated": is_simulated,
            "hour_of_day": now_ist.hour,
            "day_of_week": now_ist.weekday(),
            "is_weekend": now_ist.weekday() in [5, 6],
            "month": now_ist.month,
            "has_active_festival": len(active_fests) > 0,
            "temperature_c": weather.get("temperature_c", 28.5),
            "precipitation_mm": weather.get("precipitation_mm", 0.0),
            "weather_condition_code": weather.get("weather_code", 1),
            "created_at": now_utc
        }

        if self.db is not None:
            try:
                self.db[SNAPSHOTS_COLLECTION].insert_one(snapshot_doc)
            except Exception as e:
                logger.warning(f"[CrowdService] Failed to insert feature snapshot: {e}")

        # 5. Evaluate Blended Density with Exponential Decay
        blended_density, active_count, is_surge, anomaly_alert, _ = self._compute_decay_blending(
            place_id=request.place_id,
            city_id=city_id,
            rule_baseline_pct=rule_baseline_pct
        )

        return CrowdReportResponse(
            message=f"Thank you! Your verified report ({request.crowd_level.value.capitalize()}) has been blended into real-time crowd insights.",
            place_id=request.place_id,
            reported_density_pct=reported_density,
            blended_density_pct=blended_density,
            crowd_level=self._density_to_level(blended_density),
            active_reports_count=active_count,
            is_surge=is_surge,
            anomaly_alert=anomaly_alert
        )

    # -------------------------------------------------------------------------
    # Phase 5: Exponential Decay Engine & Anomaly Detection
    # -------------------------------------------------------------------------
    def get_live_crowd_estimate(self, place_id: str, city_id: str = "pondicherry") -> LiveCrowdResponse:
        """
        Retrieves live blended crowd density, active reporter count,
        confidence badge, and anomaly alerts for a destination.
        """
        place = places_service.get_place_by_id(place_id, city_id)
        if not place:
            other_city = "chennai" if city_id == "pondicherry" else "pondicherry"
            place = places_service.get_place_by_id(place_id, other_city)
            if place:
                city_id = other_city
            else:
                raise ValueError(f"Place with id '{place_id}' not found.")

        rule_est = self.estimate_place_crowd(city_id, place_id)
        rule_pct = rule_est["crowd_density_pct"] if rule_est else 50

        blended_density, active_count, is_surge, anomaly_alert, last_reported_time = self._compute_decay_blending(
            place_id=place_id,
            city_id=city_id,
            rule_baseline_pct=rule_pct
        )

        # Confidence badge & structured level
        if active_count >= 3:
            conf_badge = f"Verified Live ({active_count} on-site reports)"
            conf_level = "HIGH"
        elif active_count >= 1:
            conf_badge = f"Live Signal ({active_count} recent report{'s' if active_count > 1 else ''})"
            conf_level = "MEDIUM"
        else:
            conf_badge = "Rule Baseline Model"
            conf_level = "LOW"

        status_badge = self._density_to_status_badge(blended_density, is_surge)

        return LiveCrowdResponse(
            place_id=place_id,
            place_name=place.name,
            city_id=city_id,
            rule_baseline_density_pct=rule_pct,
            blended_density_pct=blended_density,
            crowd_level=self._density_to_level(blended_density),
            status_badge=status_badge,
            active_reports_count=active_count,
            is_surge=is_surge,
            anomaly_alert=anomaly_alert,
            last_reported_time=last_reported_time,
            confidence_badge=conf_badge,
            confidence_level=conf_level
        )

    def _compute_decay_blending(
        self,
        place_id: str,
        city_id: str,
        rule_baseline_pct: int
    ) -> Tuple[int, int, bool, Optional[str], Optional[str]]:
        """
        Computes weighted reported density using exponential decay:
        w_i = 0.5 ^ (delta_t / 30.0 min).
        Blends with baseline: alpha = min(0.85, 0.25 * sum(w_i)).
        Detects anomalies: 3+ distinct reports >= 2 levels above baseline.
        Returns: (blended_density, active_distinct_count, is_surge, anomaly_alert, last_reported_time_ist)
        """
        if self.db is None:
            return rule_baseline_pct, 0, False, None, None

        now = datetime.now(timezone.utc)
        two_hours_ago = now - timedelta(hours=2)

        try:
            # Query non-simulated reports from last 2 hours
            cursor = self.db[REPORTS_COLLECTION].find({
                "place_id": place_id,
                "is_simulated": False,
                "created_at": {"$gte": two_hours_ago}
            }).sort("created_at", -1)

            reports = list(cursor)
        except Exception as e:
            logger.warning(f"[CrowdService] Decay query error: {e}")
            return rule_baseline_pct, 0, False, None, None

        if not reports:
            return rule_baseline_pct, 0, False, None, None

        # Newest non-simulated report time formatted in IST
        newest_dt = reports[0]["created_at"]
        if newest_dt.tzinfo is None:
            newest_dt = newest_dt.replace(tzinfo=timezone.utc)
        last_reported_time = newest_dt.astimezone(KOLKATA_TZ).strftime("%H:%M IST")

        total_weight = 0.0
        weighted_sum = 0.0
        surge_reporters = set()
        distinct_reporters = set()

        for r in reports:
            rep_hash = r.get("reporter_hash")
            if rep_hash:
                distinct_reporters.add(rep_hash)

            r_time = r["created_at"]
            if r_time.tzinfo is None:
                r_time = r_time.replace(tzinfo=timezone.utc)

            delta_min = max(0.0, (now - r_time).total_seconds() / 60.0)
            weight = math.pow(0.5, delta_min / HALF_LIFE_MINUTES)
            density = float(r.get("reported_density_pct", 50))

            weighted_sum += weight * density
            total_weight += weight

            # Anomaly check: 3+ distinct reporters >= 20% above baseline, or overcrowded (>= 90%) within last 60m
            if (density - rule_baseline_pct >= 20.0 or density >= 90.0) and delta_min <= 60.0:
                if rep_hash:
                    surge_reporters.add(rep_hash)

        if total_weight > 0.0:
            avg_reported = weighted_sum / total_weight
            # Dynamic blending factor alpha (maxes out at 0.85 when weight >= 3.4)
            alpha = min(0.85, 0.25 * total_weight)
            blended = int(round(alpha * avg_reported + (1.0 - alpha) * rule_baseline_pct))
        else:
            blended = rule_baseline_pct

        is_surge = (len(surge_reporters) >= 3)
        anomaly_alert = None
        if is_surge:
            anomaly_alert = "⚠️ Live Crowd Surge: 3+ verified visitors have reported footfall significantly higher than normal baseline."

        return blended, len(distinct_reporters), is_surge, anomaly_alert, last_reported_time

    @staticmethod
    def _density_to_level(density: int) -> str:
        if density >= 80:
            return "peak"
        elif density >= 60:
            return "high"
        elif density >= 40:
            return "medium"
        return "low"

    @staticmethod
    def _density_to_status_badge(density: int, is_surge: bool = False) -> str:
        if is_surge:
            return "⚡ Live Surge Alert"
        if density >= 80:
            return "🟣 Overcrowded"
        elif density >= 60:
            return "🔴 Bustling"
        elif density >= 40:
            return "🟡 Moderate"
        return "🟢 Serene"


crowd_service = CrowdService()
