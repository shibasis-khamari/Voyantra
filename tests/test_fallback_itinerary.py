import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Setup paths
repo_root = Path(__file__).resolve().parent.parent
backend_path = repo_root / "backend"
sys.path.insert(0, str(backend_path))

from app.schemas.place import AgeGroupEnum, DietaryOptionEnum, CategoryEnum
from app.schemas.recommendation import ItineraryResponse
from app.services.places_service import places_service
from app.services.gemini_service import gemini_service, normalize_place_name, is_dietary_compliant

class TestFallbackItinerary(unittest.TestCase):

    def setUp(self):
        # Force GEMINI_API_KEY to empty string to ensure offline fallback engine executes
        gemini_service.api_key = ""
        places_service.reload_data()
        self.places = places_service.get_all_places("pondicherry")
        self.catalog_names = {p.name for p in self.places}
        self.catalog_map = {normalize_place_name(p.name): p for p in self.places}

    @staticmethod
    def _iter_slots(day_dict):
        """Helper iterating through slot keys, yielding (slot_key, slot) for non-null slots."""
        for slot_key in ["morning", "afternoon", "evening"]:
            slot = day_dict.get(slot_key)
            if slot and isinstance(slot, dict) and slot.get("place_name"):
                yield slot_key, slot

    def test_three_day_request_returns_three_days(self):
        """A 3-day itinerary request must return exactly 3 days with complete morning/afternoon/evening slots."""
        res = gemini_service.generate_rag_itinerary(
            query_text="3-day relaxed coastal getaway",
            retrieved_places=self.places,
            user_age=AgeGroupEnum.YOUNG_ADULT,
            user_diet=DietaryOptionEnum.ALL,
            duration_days=3,
            city_name="Pondicherry"
        )
        self.assertEqual(res["source"], "fallback")
        self.assertEqual(len(res["days"]), 3, "Must return exactly 3 days for duration_days=3")
        
        for d in res["days"]:
            self.assertIn("morning", d)
            self.assertIn("afternoon", d)
            self.assertIn("evening", d)
            for slot_key, slot in self._iter_slots(d):
                self.assertTrue(len(slot["place_name"]) > 0)
                self.assertTrue(len(slot["activity_note"]) > 0)
                self.assertTrue(len(slot["est_time"]) > 0)

    def test_strict_jain_diet_never_gets_non_jain_dining_slot(self):
        """Jain dietary preference must never be assigned a dining or cafe place that lacks pure_veg_jain."""
        res = gemini_service.generate_rag_itinerary(
            query_text="Strict Jain pilgrimage with pure veg breakfast and temples",
            retrieved_places=self.places,
            user_age=AgeGroupEnum.FAMILY,
            user_diet=DietaryOptionEnum.PURE_VEG_JAIN,
            duration_days=2,
            city_name="Pondicherry"
        )
        self.assertEqual(res["source"], "fallback")
        
        for d in res["days"]:
            for slot_key, slot in self._iter_slots(d):
                p_name = slot["place_name"]
                norm = normalize_place_name(p_name)
                if norm in self.catalog_map:
                    place_obj = self.catalog_map[norm]
                    if place_obj.category in [CategoryEnum.DINING, CategoryEnum.CAFE]:
                        opts = [opt if isinstance(opt, str) else opt.value for opt in place_obj.dietary_options]
                        self.assertIn(
                            "pure_veg_jain",
                            opts,
                            f"Place '{p_name}' assigned for Jain user does not support pure_veg_jain"
                        )

    def test_budget_equals_exact_sum_of_scheduled_places(self):
        """total_estimated_budget_inr must equal the exact sum of estimated_cost_inr for scheduled stops."""
        res = gemini_service.generate_rag_itinerary(
            query_text="Budget family vacation",
            retrieved_places=self.places,
            user_age=AgeGroupEnum.FAMILY,
            user_diet=DietaryOptionEnum.ALL,
            duration_days=2,
            city_name="Pondicherry"
        )
        scheduled_cost = 0
        for d in res["days"]:
            for slot_key, slot in self._iter_slots(d):
                p_name = slot["place_name"]
                norm = normalize_place_name(p_name)
                if norm in self.catalog_map:
                    scheduled_cost += self.catalog_map[norm].estimated_cost_inr

        self.assertEqual(
            res["total_estimated_budget_inr"],
            scheduled_cost,
            f"Budget {res['total_estimated_budget_inr']} must match sum of scheduled costs {scheduled_cost}"
        )

    def test_every_place_is_in_catalog_with_zero_invented_names(self):
        """Every scheduled place must come from the catalog; no synthetic or invented places."""
        res = gemini_service.generate_rag_itinerary(
            query_text="Explore French Quarter cafes and beaches",
            retrieved_places=self.places,
            user_age=AgeGroupEnum.ADULT,
            user_diet=DietaryOptionEnum.ALL,
            duration_days=3,
            city_name="Pondicherry"
        )
        for d in res["days"]:
            for slot_key, slot in self._iter_slots(d):
                p_name = slot["place_name"]
                self.assertNotEqual(p_name, "Free Leisure & French Cafe Rest", "Invented place detected!")
                self.assertNotEqual(p_name, "Open Leisure & Local Walk", "Invented place detected!")
                self.assertIn(
                    p_name,
                    self.catalog_names,
                    f"Place '{p_name}' does not exist in catalog!"
                )

    def test_no_duplicate_places_across_days(self):
        """No destination should be scheduled more than once across the entire multi-day itinerary."""
        res = gemini_service.generate_rag_itinerary(
            query_text="Extensive 3-day exploration of Pondicherry",
            retrieved_places=self.places,
            user_age=AgeGroupEnum.YOUNG_ADULT,
            user_diet=DietaryOptionEnum.ALL,
            duration_days=3,
            city_name="Pondicherry"
        )
        seen = []
        for d in res["days"]:
            for slot_key, slot in self._iter_slots(d):
                seen.append(slot["place_name"])

        duplicates = [name for name in seen if seen.count(name) > 1]
        self.assertEqual(len(duplicates), 0, f"Duplicate places scheduled: {set(duplicates)}")

    def test_day_1_immutability_during_day_2_refinement(self):
        """When refining Day 2, Day 1 must remain completely identical and immutable."""
        initial_res = gemini_service.generate_rag_itinerary(
            query_text="Standard 2-day tour",
            retrieved_places=self.places,
            user_age=AgeGroupEnum.ADULT,
            user_diet=DietaryOptionEnum.ALL,
            duration_days=2,
            city_name="Pondicherry"
        )
        day1_original = initial_res["days"][0]

        refinement_res = gemini_service.generate_rag_itinerary(
            query_text="Make day 2 more relaxed with afternoon tea",
            retrieved_places=self.places,
            user_age=AgeGroupEnum.ADULT,
            user_diet=DietaryOptionEnum.ALL,
            duration_days=2,
            city_name="Pondicherry",
            existing_days=initial_res["days"]
        )
        day1_refined = refinement_res["days"][0]

        for slot_key in ["morning", "afternoon", "evening"]:
            s_orig = day1_original.get(slot_key)
            s_ref = day1_refined.get(slot_key)
            if s_orig is None:
                self.assertIsNone(s_ref, f"Day 1 {slot_key} was None, but became {s_ref}")
            else:
                self.assertIsNotNone(s_ref, f"Day 1 {slot_key} was not None, but became None")
                self.assertEqual(
                    s_orig["place_name"],
                    s_ref["place_name"],
                    f"Day 1 {slot_key} place_name changed from {s_orig['place_name']} to {s_ref['place_name']}"
                )

    def test_small_catalog_omits_slots_and_invents_nothing(self):
        """With a catalog smaller than requested slots, assert no place name outside catalog,
        'Open Leisure & Local Walk' appears nowhere, non-null slots == len(places), zero duplicates,
        budget equals exact sum, and result validates against ItineraryResponse."""
        small_places = self.places[:3]
        small_names = {p.name for p in small_places}
        expected_cost = sum(p.estimated_cost_inr for p in small_places)

        res = gemini_service.generate_rag_itinerary(
            query_text="2-day trip with small catalog",
            retrieved_places=small_places,
            user_age=AgeGroupEnum.ADULT,
            user_diet=DietaryOptionEnum.ALL,
            duration_days=2,
            city_name="Pondicherry"
        )
        self.assertEqual(res["source"], "fallback")
        self.assertEqual(len(res["days"]), 2)

        # Validate against ItineraryResponse schema
        itinerary_obj = ItineraryResponse(**res)
        self.assertIsNotNone(itinerary_obj)

        non_null_slots = []
        for d in res["days"]:
            for slot_key in ["morning", "afternoon", "evening"]:
                slot = d.get(slot_key)
                if slot is not None:
                    p_name = slot.get("place_name")
                    self.assertIn(p_name, small_names, f"Place '{p_name}' not in small catalog")
                    self.assertNotEqual(p_name, "Open Leisure & Local Walk")
                    non_null_slots.append(p_name)

        self.assertEqual(len(non_null_slots), 3, f"Expected exactly 3 non-null slots, got {len(non_null_slots)}")
        self.assertEqual(len(set(non_null_slots)), 3, "No duplicate places should exist")
        self.assertEqual(res["total_estimated_budget_inr"], expected_cost)

    def test_day2_refinement_with_null_slot_in_day1(self):
        """When Day 1 has a slot set to None, Day 2 refinement must not raise and Day 1 slots remain unchanged."""
        existing_days = [
            {
                "day_number": 1,
                "theme": "Day 1 Theme",
                "morning": {"place_name": self.places[0].name, "activity_note": "Morning", "est_time": "9:00 AM"},
                "afternoon": None,
                "evening": {"place_name": self.places[1].name, "activity_note": "Evening", "est_time": "5:00 PM"}
            },
            {
                "day_number": 2,
                "theme": "Day 2 Theme",
                "morning": {"place_name": self.places[2].name, "activity_note": "Morning", "est_time": "9:00 AM"},
                "afternoon": {"place_name": self.places[3].name, "activity_note": "Afternoon", "est_time": "1:00 PM"},
                "evening": {"place_name": self.places[4].name, "activity_note": "Evening", "est_time": "5:00 PM"}
            }
        ]

        refinement_res = gemini_service.generate_rag_itinerary(
            query_text="Make day 2 more relaxed",
            retrieved_places=self.places,
            user_age=AgeGroupEnum.ADULT,
            user_diet=DietaryOptionEnum.ALL,
            duration_days=2,
            city_name="Pondicherry",
            existing_days=existing_days
        )
        self.assertEqual(refinement_res["source"], "fallback")
        day1 = refinement_res["days"][0]
        self.assertEqual(day1["morning"]["place_name"], self.places[0].name)
        self.assertIsNone(day1["afternoon"])
        self.assertEqual(day1["evening"]["place_name"], self.places[1].name)

if __name__ == "__main__":
    unittest.main()
