import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Setup paths
repo_root = Path(__file__).resolve().parent.parent
backend_path = repo_root / "backend"
sys.path.insert(0, str(backend_path))

from app.core.geo import haversine_km, PONDICHERRY_CENTER, CHENNAI_CENTER, OPERATING_RADIUS_KM
from app.services.places_service import places_service
from app.services.internet_ingestion_service import internet_ingestion_service

DATA_DIR = backend_path / "app" / "data"

class TestIngestionSafety(unittest.TestCase):

    def test_catalog_places_within_bounds_and_city_proximity(self):
        """Every place in each city file must be within 70 km of its center and closer to it than to the other."""
        cities = [
            ("pondicherry", PONDICHERRY_CENTER, CHENNAI_CENTER),
            ("chennai", CHENNAI_CENTER, PONDICHERRY_CENTER)
        ]
        for city_id, own_center, other_center in cities:
            file_path = DATA_DIR / f"{city_id}_places.json"
            self.assertTrue(file_path.exists(), f"File {file_path} must exist")
            with open(file_path, "r", encoding="utf-8") as f:
                places = json.load(f)

            self.assertGreater(len(places), 0, f"Places for {city_id} should not be empty")
            for p in places:
                lat = p["coordinates"]["lat"]
                lng = p["coordinates"]["lng"]
                dist_own = haversine_km(lat, lng, own_center[0], own_center[1])
                dist_other = haversine_km(lat, lng, other_center[0], other_center[1])

                self.assertLessEqual(
                    dist_own,
                    OPERATING_RADIUS_KM,
                    f"Place '{p['name']}' ({p['id']}) in {city_id} is {dist_own:.1f}km away (> 70km)"
                )
                self.assertLess(
                    dist_own,
                    dist_other,
                    f"Place '{p['name']}' ({p['id']}) in {city_id} is closer to other city ({dist_other:.1f}km) than own city ({dist_own:.1f}km)"
                )

    def test_mocked_ingestion_drops_out_of_bounds_and_distant_pois(self):
        """Mocked ingestion response with Hyderabad and Jaunpur coordinates drops them."""
        mock_raw = [
            # Hyderabad: Charminar (17.3616, 78.4747) -> > 500 km away
            {"name": "Charminar", "description": "Historic mosque in Hyderabad", "lat": 17.3616, "lng": 78.4747},
            # Jaunpur: Lal Darwaza Mosque (25.7534, 82.6841) -> > 1300 km away
            {"name": "Lal Darwaza Mosque", "description": "Mosque in Jaunpur UP", "lat": 25.7534, "lng": 82.6841},
            # District overview name -> should be dropped
            {"name": "Pondicherry District Overview", "description": "District administrative center", "lat": 11.9416, "lng": 79.8083},
            # Valid Pondicherry coordinate
            {"name": "Bharathi Park Heritage Lawn", "description": "Lush central park opposite Raj Nivas", "lat": 11.9335, "lng": 79.8340}
        ]

        with patch.object(internet_ingestion_service, "fetch_city_coordinates", return_value={"name": "Pondicherry", "lat": 11.9416, "lng": 79.8083}), \
             patch.object(internet_ingestion_service, "fetch_wikidata_tourist_spots", return_value=mock_raw[:2]), \
             patch.object(internet_ingestion_service, "fetch_wikipedia_articles", return_value=mock_raw[2:]):
            
            # Use temporary backup to avoid mutating real data
            pondy_file = DATA_DIR / "pondicherry_places.json"
            backup = pondy_file.read_text(encoding="utf-8")
            try:
                res = internet_ingestion_service.ingest_city_from_internet("Pondicherry")
                self.assertTrue(res["success"])
                # Charminar, Lal Darwaza, and District should have been dropped; only Bharathi Park may qualify
                ingested_names = [p["name"] for p in res["places"]]
                self.assertNotIn("Charminar", ingested_names)
                self.assertNotIn("Lal Darwaza Mosque", ingested_names)
                self.assertNotIn("Pondicherry District Overview", ingested_names)
            finally:
                pondy_file.write_text(backup, encoding="utf-8")

    def test_unsupported_city_returns_failure(self):
        """Ingestion for an unsupported city (e.g. Goa, Delhi) fails cleanly with success=False."""
        for city in ["Goa", "Delhi", "Bengaluru", "Jaipur"]:
            res = internet_ingestion_service.ingest_city_from_internet(city)
            self.assertFalse(res["success"])
            self.assertIn("strictly supports Pondicherry and Chennai", res["message"])

    def test_curated_ids_survive_and_no_duplicates_on_double_ingestion(self):
        """Curated IDs pondy-01..12 survive and double ingestion creates no duplicates."""
        pondy_file = DATA_DIR / "pondicherry_places.json"
        backup = pondy_file.read_text(encoding="utf-8")
        try:
            with open(pondy_file, "r", encoding="utf-8") as f:
                initial_places = json.load(f)
            initial_ids = {p["id"] for p in initial_places}
            self.assertIn("pondy-01", initial_ids)
            self.assertIn("pondy-12", initial_ids)

            # Ingest once with mock returning already existing place
            mock_spot = [{"name": "Promenade Beach (Rock Beach)", "description": "Duplicate test", "lat": 11.9338, "lng": 79.8358}]
            with patch.object(internet_ingestion_service, "fetch_city_coordinates", return_value={"name": "Pondicherry", "lat": 11.9416, "lng": 79.8083}), \
                 patch.object(internet_ingestion_service, "fetch_wikidata_tourist_spots", return_value=mock_spot), \
                 patch.object(internet_ingestion_service, "fetch_wikipedia_articles", return_value=[]):
                
                res1 = internet_ingestion_service.ingest_city_from_internet("Pondicherry")
                self.assertEqual(res1["total_ingested"], 0, "Duplicate should be rejected")

                # Second run
                res2 = internet_ingestion_service.ingest_city_from_internet("Pondicherry")
                self.assertEqual(res2["total_ingested"], 0, "Second run should also add 0")

            with open(pondy_file, "r", encoding="utf-8") as f:
                final_places = json.load(f)
            self.assertEqual(len(initial_places), len(final_places), "Place count should not change")
            final_ids = {p["id"] for p in final_places}
            self.assertEqual(initial_ids, final_ids, "Curated IDs must survive completely untouched")
        finally:
            pondy_file.write_text(backup, encoding="utf-8")

    def test_places_service_resolves_curated_ids(self):
        """pondy-01 and pondy-12 resolve cleanly via places_service."""
        places_service.reload_data()
        p1 = places_service.get_place_by_id("pondy-01", "pondicherry")
        self.assertIsNotNone(p1, "pondy-01 must resolve")
        self.assertEqual(p1.name, "Promenade Beach (Rock Beach)")

        p12 = places_service.get_place_by_id("pondy-12", "pondicherry")
        self.assertIsNotNone(p12, "pondy-12 must resolve")
        self.assertEqual(p12.name, "Manakula Vinayagar Temple")

if __name__ == "__main__":
    unittest.main()
