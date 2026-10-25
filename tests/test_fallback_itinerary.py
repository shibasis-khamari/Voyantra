import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Setup paths
repo_root = Path(__file__).resolve().parent.parent
backend_path = repo_root / "backend"
sys.path.insert(0, str(backend_path))

from app.schemas.place import AgeGroupEnum, DietaryOptionEnum, CategoryEnum
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
            for slot_key in ["morning", "afternoon", "evening"]:
                slot = d[slot_key]
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
            for slot_key in ["morning", "afternoon", "evening"]:
                slot = d[slot_key]
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
            for slot_key in ["morning", "afternoon", "evening"]:
                p_name = d[slot_key]["place_name"]
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
            for slot_key in ["morning", "afternoon", "evening"]:
                p_name = d[slot_key]["place_name"]
                self.assertNotEqual(p_name, "Free Leisure & French Cafe Rest", "Invented place detected!")
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
            for slot_key in ["morning", "afternoon", "evening"]:
                seen.append(d[slot_key]["place_name"])

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

        self.assertEqual(
            day1_original["morning"]["place_name"],
            day1_refined["morning"]["place_name"],
            "Day 1 morning must not change during Day 2 refinement"
        )
        self.assertEqual(
            day1_original["afternoon"]["place_name"],
            day1_refined["afternoon"]["place_name"],
            "Day 1 afternoon must not change during Day 2 refinement"
        )
        self.assertEqual(
            day1_original["evening"]["place_name"],
            day1_refined["evening"]["place_name"],
            "Day 1 evening must not change during Day 2 refinement"
        )

if __name__ == "__main__":
    unittest.main()
