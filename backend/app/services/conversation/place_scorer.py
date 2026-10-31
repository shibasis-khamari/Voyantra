"""
Voyantra 2.0 Multi-Factor Place Selection & Scoring Engine
Ranks places according to user intent, interests, age suitability,
budget tiers, dietary constraints, category diversity, and data provenance.
"""
import logging
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Set, Union
from ...schemas.place import Place, CategoryEnum, DietaryOptionEnum

logger = logging.getLogger(__name__)

class PlaceScorer:
    """
    Evaluates and scores candidate attractions and dining spots
    using a multi-factor weighting formula.
    """

    WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    def is_place_closed_on_date(self, place: Any, date_str: Optional[str]) -> bool:
        """
        Returns True if the place is known to be closed on the specified ISO date (YYYY-MM-DD).
        If date_str is None or invalid, returns False.
        """
        if not date_str or not hasattr(place, "weekly_closing_days") or not place.weekly_closing_days:
            return False
        try:
            dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
            weekday_name = self.WEEKDAY_NAMES[dt.weekday()]
            closing_days = [d.strip().capitalize() for d in place.weekly_closing_days]
            return weekday_name in closing_days
        except Exception as e:
            logger.debug(f"Date parsing failed for {date_str}: {e}")
            return False

    def check_dietary_compatibility(self, place: Any, dietary: Optional[str]) -> bool:
        """
        Evaluates strict dietary constraint compliance for dining/cafe venues.
        Non-dining places return True.
        If user requires strict dietary compliance (e.g. pure_veg_jain, vegan, halal, veg)
        and the dining venue does not support it, returns False.
        """
        cat_val = place.category.value if hasattr(place.category, "value") else str(place.category or "")
        if cat_val not in ["cafe", "dining"]:
            return True

        if not dietary or dietary.lower() in ["all", "any", "none"]:
            return True

        d_lower = dietary.lower().replace("-", "_").strip()
        opts = [
            (opt.value if hasattr(opt, "value") else str(opt)).lower().replace("-", "_")
            for opt in getattr(place, "dietary_options", [])
        ]

        if "jain" in d_lower or "pure_veg_jain" in d_lower:
            return any("jain" in opt or "pure_veg_jain" in opt for opt in opts)
        if "vegan" in d_lower:
            return any("vegan" in opt for opt in opts)
        if "halal" in d_lower:
            return any("halal" in opt for opt in opts)
        if "pure_veg" in d_lower:
            return any("pure_veg" in opt or "vegetarian" in opt for opt in opts)
        if "veg" in d_lower:
            return any("veg" in opt for opt in opts)

        return True

    def score_place(
        self,
        place: Any,
        criteria: Dict[str, Any],
        current_slot: str = "morning",
        day_history: Optional[List[Any]] = None,
        used_place_ids: Optional[Set[str]] = None,
        mandatory_ids: Optional[Set[str]] = None
    ) -> float:
        """
        Computes composite multi-factor score for a place.
        Returns float score. Incompatible places return -float('inf').
        """
        p_id = getattr(place, "id", "")
        p_cat = place.category.value if hasattr(place.category, "value") else str(place.category or "")
        mandatory_set = mandatory_ids or set()
        used_set = used_place_ids or set()

        # 1. Duplicate check within the active alternative's global tracker
        # If place has already been scheduled and is NOT a mandatory requested revisit,
        # eliminate it completely.
        if p_id in used_set and p_id not in mandatory_set:
            return -float("inf")

        # 2. Strict weekly closing check
        travel_date = criteria.get("travel_date")
        if self.is_place_closed_on_date(place, travel_date):
            # If mandatory requested, do not completely drop, but penalize heavily so user can be warned
            if p_id in mandatory_set:
                return -50.0
            return -float("inf")

        # 3. Strict dietary check for dining venues
        user_diet = criteria.get("dietary") or criteria.get("dietary_preference") or "all"
        if not self.check_dietary_compatibility(place, user_diet):
            return -float("inf")

        score: float = 0.0

        # ----------------------------------------------------------------------
        # Mandatory place priority bonus (never drop user requested places)
        # ----------------------------------------------------------------------
        if p_id in mandatory_set:
            score += 100.0

        # ----------------------------------------------------------------------
        # Sightseeing vs Dining Slot Category Separation
        # ----------------------------------------------------------------------
        is_dining_slot = current_slot in ["lunch", "dinner", "meal"]
        is_dining_venue = p_cat in ["cafe", "dining"]

        if is_dining_slot:
            if is_dining_venue:
                score += 35.0
            else:
                score -= 40.0
        else:
            # Sightseeing slot (morning, afternoon, evening)
            if is_dining_venue:
                # Do not fill main sightseeing slots with standard restaurants
                score -= 50.0
            else:
                # Prioritize major attractions for primary sightseeing
                is_major = getattr(place, "is_major_attraction", True)
                if is_major:
                    score += 25.0

        # ----------------------------------------------------------------------
        # User Interest Alignment
        # ----------------------------------------------------------------------
        user_interests = criteria.get("interests") or []
        if isinstance(user_interests, str):
            user_interests = [i.strip() for i in user_interests.split(",") if i.strip()]

        place_tags = [t.lower() for t in getattr(place, "tags", [])]
        place_niche = [n.lower() for n in getattr(place, "niche_interests", [])]
        place_desc = (getattr(place, "description", "") or "").lower()
        sub_cat = (getattr(place, "sub_category", "") or "").lower()

        interest_matches = 0
        for interest in user_interests:
            intr = interest.lower().strip()
            if not intr:
                continue
            if (intr in p_cat.lower() or
                intr in sub_cat or
                any(intr in tag for tag in place_tags) or
                any(intr in n for n in place_niche) or
                intr in place_desc):
                interest_matches += 1

        score += min(interest_matches * 25.0, 75.0)

        # ----------------------------------------------------------------------
        # Age Group Suitability
        # ----------------------------------------------------------------------
        age_group = (criteria.get("age_group") or "all").lower()
        acc_rating = getattr(place, "accessibility_rating", 0) or 0
        wheelchair_ok = acc_rating >= 4 or getattr(place, "wheelchair_accessible", False)
        kid_friendly = getattr(place, "kid_friendly", True)
        exertion = getattr(place, "physical_exertion", "moderate")

        if "senior" in age_group:
            if wheelchair_ok:
                score += 15.0
            if exertion == "low":
                score += 10.0
            elif exertion == "high":
                score -= 25.0
            if p_cat in ["spiritual", "heritage", "nature"]:
                score += 10.0
            elif p_cat == "adventure":
                score -= 30.0
        elif "fam" in age_group or "kid" in age_group:
            if kid_friendly or "kid_friendly" in place_tags:
                score += 15.0
            if p_cat in ["nature", "beach", "culture"]:
                score += 10.0
            if exertion == "high":
                score -= 10.0
        elif "young" in age_group:
            if p_cat in ["adventure", "beach", "cafe"]:
                score += 15.0
            if "surfing" in place_tags or "nightlife" in place_tags or "watersports" in place_tags:
                score += 15.0

        # ----------------------------------------------------------------------
        # Budget Tier Compatibility
        # ----------------------------------------------------------------------
        budget_tier = (criteria.get("budget_tier") or criteria.get("budget") or "moderate").lower()
        cost = getattr(place, "estimated_cost_inr", 0) or 0

        if "budget" in budget_tier:
            if cost == 0:
                score += 15.0
            elif cost <= 250:
                score += 10.0
            elif cost > 1000:
                score -= 20.0
        elif "luxury" in budget_tier:
            if cost > 500 or "luxury" in place_tags or "heritage" in place_tags:
                score += 15.0

        # ----------------------------------------------------------------------
        # Data Verification Status Bonus
        # ----------------------------------------------------------------------
        v_status = getattr(place, "verification_status", "unverified")
        if v_status == "verified":
            score += 5.0

        # ----------------------------------------------------------------------
        # Category Diversity & Monotony Prevention (within the same day)
        # ----------------------------------------------------------------------
        if day_history:
            same_cat_count = 0
            for prev_place in day_history:
                prev_cat = getattr(prev_place, "category", None)
                prev_cat_val = prev_cat.value if hasattr(prev_cat, "value") else str(prev_cat or "")
                if prev_cat_val == p_cat:
                    same_cat_count += 1

            if same_cat_count == 1:
                score -= 15.0
            elif same_cat_count >= 2:
                score -= 35.0

        return score

    def rank_candidate_places(
        self,
        candidates: List[Any],
        criteria: Dict[str, Any],
        current_slot: str = "morning",
        day_history: Optional[List[Any]] = None,
        used_place_ids: Optional[Set[str]] = None,
        mandatory_ids: Optional[Set[str]] = None
    ) -> List[tuple]:
        """
        Ranks candidate places and returns list of (place, score) tuples
        sorted in descending order of score, excluding incompatible items.
        """
        scored = []
        for p in candidates:
            s = self.score_place(
                place=p,
                criteria=criteria,
                current_slot=current_slot,
                day_history=day_history,
                used_place_ids=used_place_ids,
                mandatory_ids=mandatory_ids
            )
            if s > -float("inf"):
                scored.append((p, s))

        scored.sort(key=lambda item: item[1], reverse=True)
        return scored

    def extract_mandatory_place_ids(self, text: str, available_places: List[Any]) -> Set[str]:
        """
        Detects explicitly requested places in natural language user prompts
        and returns matching place IDs.
        """
        if not text:
            return set()

        text_lower = text.lower()
        matched_ids = set()

        # Sort places by name length descending to match specific names first
        sorted_places = sorted(available_places, key=lambda p: len(getattr(p, "name", "")), reverse=True)

        for p in sorted_places:
            p_name = getattr(p, "name", "")
            if not p_name:
                continue
            name_clean = re.sub(r'[\(,\-].*?\)', '', p_name).split('&')[0].split(',')[0].strip().lower()

            # Exact name or clean base match
            if name_clean and len(name_clean) >= 4 and name_clean in text_lower:
                matched_ids.add(p.id)
            elif p_name.lower() in text_lower:
                matched_ids.add(p.id)

        return matched_ids

place_scorer = PlaceScorer()
