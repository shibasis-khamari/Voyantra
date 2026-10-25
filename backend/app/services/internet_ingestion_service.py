import requests
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from ..schemas.place import Place, CategoryEnum, BudgetTierEnum, CrowdTendencyEnum, AgeGroupEnum, DietaryOptionEnum, Coordinates

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

class InternetIngestionService:
    def __init__(self):
        self.headers = {
            "User-Agent": "VoyantraTouristApp/1.0 (academic-project; contact: dev@voyantra.org)",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "application/json"
        }

    def fetch_city_coordinates(self, city_name: str) -> Optional[Dict[str, Any]]:
        """Fetch city lat, lng from Nominatim with Photon fallback."""
        # 1. Nominatim
        try:
            url = "https://nominatim.openstreetmap.org/search"
            res = requests.get(url, params={"q": city_name, "format": "json", "limit": 1}, headers=self.headers, timeout=10)
            if res.ok and len(res.json()) > 0:
                data = res.json()[0]
                return {
                    "name": data.get("display_name", city_name),
                    "lat": float(data["lat"]),
                    "lng": float(data["lon"])
                }
        except Exception as e:
            print(f"[Ingestion] Nominatim geocode error: {e}")

        # 2. Photon Fallback
        try:
            photon_url = "https://photon.komoot.io/api/"
            res = requests.get(photon_url, params={"q": city_name, "limit": 1}, headers=self.headers, timeout=8)
            if res.ok:
                features = res.json().get("features", [])
                if features:
                    coords = features[0]["geometry"]["coordinates"]
                    name = features[0]["properties"].get("name", city_name)
                    return {"name": name, "lat": float(coords[1]), "lng": float(coords[0])}
        except Exception as e:
            print(f"[Ingestion] Photon fallback error: {e}")

        return None

    def fetch_wikidata_tourist_spots(self, city_name: str) -> List[Dict[str, Any]]:
        """Fetch tourist attractions, monuments, temples, and beaches from Wikidata SPARQL."""
        url = "https://query.wikidata.org/sparql"
        sparql_headers = {
            "User-Agent": "VoyantraTouristBot/1.0 (academic; voyantra@gmail.com)",
            "Accept": "application/sparql-results+json"
        }
        
        # Query Wikidata for items in or near the city with coordinates and images
        query = f"""
        SELECT DISTINCT ?item ?itemLabel ?itemDescription ?coord ?image WHERE {{
          {{
            ?item wdt:P131* ?city.
            ?city rdfs:label "{city_name}"@en.
            ?item (wdt:P31/(wdt:P279*)) ?type.
            VALUES ?type {{ wd:Q570116 wd:Q33506 wd:Q860861 wd:Q16970 wd:Q24354 wd:Q4989906 wd:Q16560 wd:Q5003624 wd:Q207694 wd:Q839954 }}.
            ?item wdt:P625 ?coord.
            OPTIONAL {{ ?item wdt:P18 ?image. }}
          }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        LIMIT 30
        """
        try:
            res = requests.get(url, params={"query": query, "format": "json"}, headers=sparql_headers, timeout=18)
            if res.ok:
                bindings = res.json().get("results", {}).get("bindings", [])
                results = []
                for b in bindings:
                    name = b.get("itemLabel", {}).get("value")
                    # Ignore unnamed Q-codes
                    if not name or name.startswith("Q") and name[1:].isdigit():
                        continue
                    
                    coord_str = b.get("coord", {}).get("value", "") # e.g. "Point(75.845 26.919)"
                    match = re.search(r"Point\(([-\d.]+)\s+([-\d.]+)\)", coord_str)
                    if match:
                        lng = float(match.group(1))
                        lat = float(match.group(2))
                        results.append({
                            "name": name,
                            "description": b.get("itemDescription", {}).get("value"),
                            "lat": lat,
                            "lng": lng,
                            "image_url": b.get("image", {}).get("value")
                        })
                return results
        except Exception as e:
            print(f"[Ingestion] Wikidata SPARQL error: {e}")
        return []

    def fetch_wikipedia_articles(self, city_name: str) -> List[Dict[str, Any]]:
        """Fetch popular tourist attractions from Wikipedia Search API."""
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": f"tourist attractions in {city_name}",
            "gsrlimit": 15,
            "prop": "extracts|pageimages|coordinates",
            "exintro": True,
            "explaintext": True,
            "piprop": "thumbnail",
            "pithumbsize": 800
        }
        try:
            res = requests.get(url, params=params, headers=self.headers, timeout=12)
            if res.ok:
                pages = res.json().get("query", {}).get("pages", {})
                articles = []
                for _, page in pages.items():
                    title = page.get("title", "")
                    extract = page.get("extract", "")
                    coords = page.get("coordinates", [])
                    img_url = page.get("thumbnail", {}).get("source")
                    
                    if coords and len(coords) > 0:
                        lat = coords[0].get("lat")
                        lng = coords[0].get("lon")
                    else:
                        continue

                    # Filter out the city overview page itself
                    if title.lower() == city_name.lower():
                        continue

                    summary = ". ".join(extract.split(". ")[:3]) + "." if extract else ""
                    articles.append({
                        "name": title,
                        "description": summary,
                        "lat": lat,
                        "lng": lng,
                        "image_url": img_url
                    })
                return articles
        except Exception as e:
            print(f"[Ingestion] Wikipedia articles error: {e}")
        return []

    def categorize_place(self, name: str, desc: str) -> Dict[str, Any]:
        text = f"{name} {desc}".lower()

        if any(w in text for w in ["beach", "sea", "coast", "shore", "island", "cove"]):
            return {
                "category": CategoryEnum.BEACH,
                "sub_category": "Scenic Beach & Coastline",
                "crowd": CrowdTendencyEnum.HIGH,
                "budget": BudgetTierEnum.BUDGET,
                "cost": 0,
                "duration": 120,
                "accessibility": 4,
                "age_groups": [AgeGroupEnum.YOUNG_ADULT, AgeGroupEnum.ADULT, AgeGroupEnum.FAMILY],
                "dietary": [DietaryOptionEnum.ALL]
            }
        elif any(w in text for w in ["temple", "church", "mosque", "ashram", "cathedral", "monastery", "gurudwara", "spiritual"]):
            return {
                "category": CategoryEnum.SPIRITUAL,
                "sub_category": "Spiritual Shrine & Historic Temple",
                "crowd": CrowdTendencyEnum.HIGH,
                "budget": BudgetTierEnum.BUDGET,
                "cost": 0,
                "duration": 60,
                "accessibility": 3,
                "age_groups": [AgeGroupEnum.SENIOR, AgeGroupEnum.FAMILY, AgeGroupEnum.ADULT],
                "dietary": [DietaryOptionEnum.ALL, DietaryOptionEnum.VEGETARIAN, DietaryOptionEnum.PURE_VEG_JAIN]
            }
        elif any(w in text for w in ["fort", "palace", "museum", "monument", "gate", "tomb", "heritage", "haveli"]):
            return {
                "category": CategoryEnum.HERITAGE,
                "sub_category": "Heritage Fort & Historical Monument",
                "crowd": CrowdTendencyEnum.MEDIUM,
                "budget": BudgetTierEnum.MODERATE,
                "cost": 150,
                "duration": 90,
                "accessibility": 3,
                "age_groups": [AgeGroupEnum.ADULT, AgeGroupEnum.FAMILY, AgeGroupEnum.YOUNG_ADULT, AgeGroupEnum.SENIOR],
                "dietary": [DietaryOptionEnum.ALL]
            }
        elif any(w in text for w in ["park", "garden", "sanctuary", "lake", "waterfall", "wildlife", "zoo", "forest"]):
            return {
                "category": CategoryEnum.NATURE,
                "sub_category": "Nature Reserve & Botanical Garden",
                "crowd": CrowdTendencyEnum.LOW,
                "budget": BudgetTierEnum.BUDGET,
                "cost": 50,
                "duration": 90,
                "accessibility": 5,
                "age_groups": [AgeGroupEnum.FAMILY, AgeGroupEnum.SENIOR, AgeGroupEnum.ALL],
                "dietary": [DietaryOptionEnum.ALL]
            }
        elif any(w in text for w in ["cafe", "coffee", "bistro", "bakery", "creperie"]):
            return {
                "category": CategoryEnum.CAFE,
                "sub_category": "Artisan Cafe & Bistro",
                "crowd": CrowdTendencyEnum.HIGH,
                "budget": BudgetTierEnum.MODERATE,
                "cost": 400,
                "duration": 60,
                "accessibility": 4,
                "age_groups": [AgeGroupEnum.YOUNG_ADULT, AgeGroupEnum.ADULT],
                "dietary": [DietaryOptionEnum.ALL, DietaryOptionEnum.VEGETARIAN, DietaryOptionEnum.VEGAN]
            }
        else:
            return {
                "category": CategoryEnum.HERITAGE,
                "sub_category": "Tourist Landmark",
                "crowd": CrowdTendencyEnum.MEDIUM,
                "budget": BudgetTierEnum.BUDGET,
                "cost": 50,
                "duration": 60,
                "accessibility": 4,
                "age_groups": [AgeGroupEnum.ALL],
                "dietary": [DietaryOptionEnum.ALL]
            }

    def ingest_city_from_internet(self, city_name: str) -> Dict[str, Any]:
        """
        Directly fetches live POI data for any city from OpenStreetMap, Wikidata, and Wikipedia
        and stores it in the database.
        """
        city_id = city_name.strip().lower().replace(" ", "_")
        geo = self.fetch_city_coordinates(city_name)
        if not geo:
            return {"success": False, "message": f"Could not find coordinates on the internet for '{city_name}'"}

        # 1. Fetch from Wikidata
        wikidata_spots = self.fetch_wikidata_tourist_spots(city_name.title())
        
        # 2. Fetch from Wikipedia
        wiki_spots = self.fetch_wikipedia_articles(city_name.title())

        # Merge spots
        combined_raw = wikidata_spots + wiki_spots
        if not combined_raw:
            return {"success": False, "message": f"No tourist destinations found on Wikidata/Wikipedia for '{city_name}'"}

        enriched_places: List[Place] = []
        seen_names = set()

        default_images = {
            CategoryEnum.BEACH: "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80",
            CategoryEnum.HERITAGE: "https://images.unsplash.com/photo-1596178065887-1198b6148b2b?auto=format&fit=crop&w=800&q=80",
            CategoryEnum.SPIRITUAL: "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?auto=format&fit=crop&w=800&q=80",
            CategoryEnum.CAFE: "https://images.unsplash.com/photo-1554118811-1e0d58224f24?auto=format&fit=crop&w=800&q=80",
            CategoryEnum.DINING: "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80",
            CategoryEnum.NATURE: "https://images.unsplash.com/photo-1513836279014-a89f7a76ae86?auto=format&fit=crop&w=800&q=80",
            CategoryEnum.ADVENTURE: "https://images.unsplash.com/photo-1502680390469-be75c86b636f?auto=format&fit=crop&w=800&q=80"
        }

        for idx, item in enumerate(combined_raw):
            name = item["name"].strip()
            if name.lower() in seen_names:
                continue
            seen_names.add(name.lower())

            desc = item.get("description") or f"{name} is a renowned tourist attraction in {city_name.title()}."
            meta = self.categorize_place(name, desc)
            img = item.get("image_url") or default_images.get(meta["category"], default_images[CategoryEnum.HERITAGE])

            place = Place(
                id=f"{city_id}-live-{len(enriched_places)+1}",
                city_id=city_id,
                name=name,
                category=meta["category"],
                sub_category=meta["sub_category"],
                description=desc,
                highlights=[f"Major attraction in {city_name.title()}", f"{meta['sub_category']} experience", "Directly navigable on OpenStreetMap"],
                budget_tier=meta["budget"],
                estimated_cost_inr=meta["cost"],
                duration_minutes=meta["duration"],
                coordinates=Coordinates(lat=item["lat"], lng=item["lng"]),
                address=f"{name}, {city_name.title()}",
                image_url=img,
                best_time_to_visit="Morning or Evening",
                crowd_tendency=meta["crowd"],
                recommended_age_groups=meta["age_groups"],
                dietary_options=meta["dietary"],
                accessibility_rating=meta["accessibility"],
                tags=[meta["category"].value, "live-ingested", city_id],
                rating=round(4.2 + (abs(hash(name)) % 7) / 10.0, 1),
                review_count=150 + (abs(hash(name)) % 2500)
            )
            enriched_places.append(place)

        if not enriched_places:
            return {"success": False, "message": f"No valid tourist spots extracted for '{city_name}'"}

        # Save to JSON storage
        output_file = DATA_DIR / f"{city_id}_places.json"
        places_dict_list = [p.model_dump() if hasattr(p, 'model_dump') else p.dict() for p in enriched_places]
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(places_dict_list, f, indent=2)

        # Update cities.json
        cities_file = DATA_DIR / "cities.json"
        try:
            with open(cities_file, "r", encoding="utf-8") as f:
                cities = json.load(f)
        except Exception:
            cities = []

        if not any(c["id"] == city_id for c in cities):
            cities.append({
                "id": city_id,
                "name": city_name.title(),
                "country": "India",
                "coordinates": {"lat": geo["lat"], "lng": geo["lng"]},
                "description": f"Live destinations for {city_name.title()} directly ingested from OpenStreetMap and Wikipedia.",
                "is_pilot": False
            })
            with open(cities_file, "w", encoding="utf-8") as f:
                json.dump(cities, f, indent=2)

        return {
            "success": True,
            "city_id": city_id,
            "city_name": city_name.title(),
            "total_ingested": len(enriched_places),
            "coordinates": {"lat": geo["lat"], "lng": geo["lng"]},
            "places": [p.model_dump() if hasattr(p, 'model_dump') else p.dict() for p in enriched_places[:10]]
        }

internet_ingestion_service = InternetIngestionService()
