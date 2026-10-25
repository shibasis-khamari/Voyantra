import logging
import itertools
from typing import List, Dict, Any, Optional, Tuple
from ..schemas.place import Coordinates
from ..schemas.route import (
    DayOptimizationSlot,
    OptimizedDaySlot,
    TransitLeg,
    DayOptimizationRequest,
    DayOptimizationResponse,
    RouteModeEnum,
    RoutingTier,
)
from .routing_service import routing_service

logger = logging.getLogger(__name__)

# Standard anchor target windows (in minutes from midnight)
ANCHOR_WINDOWS = {
    "morning": (540, 720),     # 09:00 - 12:00
    "lunch": (720, 870),       # 12:00 - 14:30
    "afternoon": (840, 1020),   # 14:00 - 17:00
    "sunset": (1020, 1140),    # 17:00 - 19:00
    "pooja": (390, 720),       # 06:30 - 12:00 (or 17:00 - 20:30)
    "evening": (1050, 1260),   # 17:30 - 21:00
    "dinner": (1170, 1320),    # 19:30 - 22:00
}


def time_str_to_minutes(t_str: str) -> int:
    """Converts 'HH:MM' string to minutes from midnight."""
    try:
        parts = t_str.split(":")
        return int(parts[0]) * 60 + int(parts[1])
    except Exception:
        return 540  # Default 09:00


def minutes_to_time_str(mins: int) -> str:
    """Converts minutes from midnight to 'HH:MM' string."""
    h = int(mins // 60) % 24
    m = int(mins % 60)
    return f"{h:02d}:{m:02d}"


class TSPService:
    def optimize_day(self, request: DayOptimizationRequest) -> DayOptimizationResponse:
        """
        Solves Time-Constrained TSP with Anchored Slots.
        1. Identifies fixed / anchored stops (sunset, pooja, meals, user-locked).
        2. Queries N x N travel matrix for inter-stop travel times and distances.
        3. Optimizes placement of flexible stops around fixed anchors to minimize travel time.
        4. Evaluates schedule gaps, opening hours warnings, and festival road closure flags.
        """
        slots = request.slots
        n = len(slots)
        if n == 0:
            raise ValueError("At least 1 slot required for optimization.")

        # Single stop edge-case
        if n == 1:
            s0 = slots[0]
            start_m = time_str_to_minutes(request.day_start_time)
            end_m = start_m + s0.visit_duration_minutes
            warn = None
            if not s0.opening_hours or not s0.opening_hours.is_verified:
                warn = "Hours not verified; please confirm opening times locally on arrival."

            opt_slot = OptimizedDaySlot(
                order=1,
                slot_id=s0.slot_id,
                place_name=s0.place_name,
                place_id=s0.place_id,
                coordinates=s0.coordinates,
                start_time=minutes_to_time_str(start_m),
                end_time=minutes_to_time_str(end_m),
                visit_duration_minutes=s0.visit_duration_minutes,
                is_locked=s0.is_locked,
                time_anchor=s0.time_anchor,
                hours_warning=warn
            )
            return DayOptimizationResponse(
                day_number=request.day_number,
                city_id=request.city_id,
                mode=request.mode,
                optimized_slots=[opt_slot],
                transit_legs=[],
                total_travel_time_minutes=0.0,
                total_travel_distance_km=0.0,
                total_visit_time_minutes=float(s0.visit_duration_minutes),
                tier_summary={RoutingTier.local_osrm.value: 1},
                is_approximate=False
            )

        # 1. Query N x N travel matrix
        matrix_coords = [s.coordinates for s in slots]
        matrix_res = routing_service.get_matrix(
            coordinates=matrix_coords,
            mode=request.mode,
            city_id=request.city_id
        )
        durations = matrix_res.durations_minutes
        distances = matrix_res.distances_km

        # 2. Determine target time windows for each slot
        slot_windows: List[Tuple[int, int]] = []
        for s in slots:
            w_start, w_end = 540, 1320  # Default entire day 09:00 - 22:00
            if s.fixed_time_window:
                w_start = time_str_to_minutes(s.fixed_time_window.get("start", "09:00"))
                w_end = time_str_to_minutes(s.fixed_time_window.get("end", "22:00"))
            elif s.time_anchor and s.time_anchor.lower() in ANCHOR_WINDOWS:
                w_start, w_end = ANCHOR_WINDOWS[s.time_anchor.lower()]

            slot_windows.append((w_start, w_end))

        # 3. Check for fixed/locked indices
        indices = list(range(n))
        locked_indices = {i for i in indices if slots[i].is_locked}
        anchored_indices = {i for i in indices if slots[i].time_anchor in ["sunset", "lunch", "dinner", "pooja"]}

        # If all slots are locked, sequence is completely preserved
        if len(locked_indices) == n:
            best_sequence = indices
        else:
            # Evaluate feasible permutations that respect anchor ordering
            # For n <= 8, permutations are small (<= 40,320); for n=9, 10, filter candidates
            best_sequence = None
            best_score = float("inf")

            # Candidate permutations: preserve locked slots at their exact positions
            candidate_perms = itertools.permutations(indices)

            for perm in candidate_perms:
                # Check locked slot constraint
                valid_locked = True
                for idx in locked_indices:
                    if perm[idx] != idx:
                        valid_locked = False
                        break
                if not valid_locked:
                    continue

                # Evaluate travel time + window penalty
                travel_time = 0.0
                window_penalty = 0.0
                cur_time = time_str_to_minutes(request.day_start_time)

                for step_idx in range(n):
                    slot_i = perm[step_idx]
                    win_start, win_end = slot_windows[slot_i]

                    # If arriving after window end, penalize heavily
                    if cur_time > win_end:
                        window_penalty += (cur_time - win_end) * 5.0
                    elif cur_time < win_start:
                        # Waiting for slot to open (e.g. sunset waiting)
                        wait = win_start - cur_time
                        window_penalty += wait * 1.0
                        cur_time = win_start

                    # Add visit duration
                    cur_time += slots[slot_i].visit_duration_minutes

                    # Add travel time to next slot
                    if step_idx < n - 1:
                        next_slot = perm[step_idx + 1]
                        leg_time = durations[slot_i][next_slot]
                        travel_time += leg_time
                        cur_time += leg_time

                total_score = travel_time + window_penalty
                if total_score < best_score:
                    best_score = total_score
                    best_sequence = list(perm)

            if not best_sequence:
                best_sequence = indices

        # 4. Construct final optimized schedule with exact times
        optimized_slots: List[OptimizedDaySlot] = []
        transit_legs: List[TransitLeg] = []
        cur_mins = time_str_to_minutes(request.day_start_time)

        total_travel_time = 0.0
        total_travel_distance = 0.0
        total_visit_time = 0.0

        for order_idx, slot_idx in enumerate(best_sequence, start=1):
            s = slots[slot_idx]
            w_start, w_end = slot_windows[slot_idx]

            # Adjust start time if early for an anchor (e.g. sunset)
            if cur_mins < w_start and s.time_anchor in ["sunset", "lunch", "dinner"]:
                cur_mins = w_start

            start_str = minutes_to_time_str(cur_mins)
            end_mins = cur_mins + s.visit_duration_minutes
            end_str = minutes_to_time_str(end_mins)
            total_visit_time += s.visit_duration_minutes

            hours_warn = None
            if not s.opening_hours or not s.opening_hours.is_verified:
                hours_warn = "Hours not verified; please confirm opening times locally on arrival."

            optimized_slots.append(
                OptimizedDaySlot(
                    order=order_idx,
                    slot_id=s.slot_id,
                    place_name=s.place_name,
                    place_id=s.place_id,
                    coordinates=s.coordinates,
                    start_time=start_str,
                    end_time=end_str,
                    visit_duration_minutes=s.visit_duration_minutes,
                    is_locked=s.is_locked,
                    time_anchor=s.time_anchor,
                    hours_warning=hours_warn
                )
            )

            # Build transit leg to next stop
            if order_idx < len(best_sequence):
                next_slot_idx = best_sequence[order_idx]
                next_s = slots[next_slot_idx]

                dep_str = end_str
                # Fetch route polyline and closure warning between stops
                route_res = routing_service.get_route(
                    origin_lat=s.coordinates.lat,
                    origin_lng=s.coordinates.lng,
                    dest_lat=next_s.coordinates.lat,
                    dest_lng=next_s.coordinates.lng,
                    mode=request.mode,
                    city_id=request.city_id,
                    travel_date=request.travel_date
                )

                leg_dur = route_res.estimated_travel_time_minutes
                leg_dist = route_res.distance_km
                arr_mins = end_mins + leg_dur
                arr_str = minutes_to_time_str(arr_mins)

                transit_legs.append(
                    TransitLeg(
                        from_place=s.place_name,
                        to_place=next_s.place_name,
                        distance_km=leg_dist,
                        duration_minutes=leg_dur,
                        tier_used=route_res.tier_used,
                        walking_source=route_res.walking_source,
                        is_approximate=route_res.is_approximate,
                        departure_time=dep_str,
                        arrival_time=arr_str,
                        closure_affected=route_res.closure_affected,
                        closure_warning=route_res.closure_warning,
                        polyline_geojson=route_res.polyline_geojson
                    )
                )

                total_travel_time += leg_dur
                total_travel_distance += leg_dist
                cur_mins = arr_mins

        return DayOptimizationResponse(
            day_number=request.day_number,
            city_id=request.city_id,
            mode=request.mode,
            optimized_slots=optimized_slots,
            transit_legs=transit_legs,
            total_travel_time_minutes=round(total_travel_time, 1),
            total_travel_distance_km=round(total_travel_distance, 3),
            total_visit_time_minutes=float(total_visit_time),
            tier_summary=matrix_res.tier_summary,
            is_approximate=matrix_res.is_approximate
        )


tsp_service = TSPService()
