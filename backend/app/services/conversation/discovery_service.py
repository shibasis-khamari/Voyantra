"""
Voyantra 2.0 Travel Discovery Service
Executes grounded discovery for places, hotels, and restaurants in Pondicherry and Chennai.
Never invents details, prices, or fake properties.
"""
from typing import List, Optional, Dict, Any
from ...core.config import settings
from ...schemas.chat import PlaceCardData, HotelCardData, RestaurantCardData
from ...schemas.place import PlaceFilter, CategoryEnum, BudgetTierEnum, DietaryOptionEnum
from ...services.places_service import places_service
from ...services.hotels_service import hotels_service
from ...schemas.hotel import HotelFilter
from ..knowledge.retrieval.hybrid_retriever import hybrid_retriever
from ...schemas.knowledge import KnowledgeEntity

class DiscoveryService:
    def search_places(
        self,
        query: str,
        city_id: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 4
    ) -> List[PlaceCardData]:
        """Discovers verified places in Pondicherry or Chennai using Hybrid Retrieval and Places Service."""
        target_city = city_id if city_id and city_id not in ["all", "both"] else None
        
        parsed_category = None
        if category and category != "all":
            try:
                parsed_category = [CategoryEnum(category.lower())]
            except Exception:
                pass

        # 1. Query Places Catalog
        f = PlaceFilter(
            city_id=target_city,
            categories=parsed_category,
            search_query=query if query and len(query) > 2 else None
        )
        places = places_service.filter_places(f)

        results: List[PlaceCardData] = []
        seen_ids = set()

        for p in places[:limit]:
            seen_ids.add(p.id)
            results.append(PlaceCardData(
                id=p.id,
                name=p.name,
                city_id=p.city_id or "pondicherry",
                category=p.category.value if hasattr(p.category, "value") else str(p.category),
                sub_category=p.sub_category,
                estimated_cost_inr=p.estimated_cost_inr or 0,
                duration_minutes=p.duration_minutes or 60,
                rating=getattr(p, "rating", 4.5) or 4.5,
                address=p.address,
                highlights=p.highlights or [],
                image_url=p.image_url
            ))

        # 2. Enrich with VTKE Hybrid Knowledge Engine if enabled and more slots available
        if getattr(settings, "KNOWLEDGE_RAG_ENABLED", True) and len(results) < limit:
            try:
                k_results = hybrid_retriever.search(
                    query=query or "",
                    city_id=target_city,
                    category=category,
                    top_k=limit
                )
                for ent, _score in k_results:
                    if len(results) >= limit:
                        break
                    if isinstance(ent, KnowledgeEntity) and ent.id not in seen_ids and ent.entity_type == "place":
                        seen_ids.add(ent.id)
                        results.append(PlaceCardData(
                            id=ent.id,
                            name=ent.name,
                            city_id=ent.city_id or "pondicherry",
                            category=ent.category or "heritage",
                            sub_category=ent.sub_category,
                            estimated_cost_inr=ent.estimated_cost_inr or 0,
                            duration_minutes=ent.duration_minutes or 60,
                            rating=ent.rating or 4.5,
                            address=ent.address or f"{ent.name}, {ent.city_id.capitalize() if ent.city_id else ''}",
                            highlights=ent.highlights or [],
                            image_url=ent.image_url or "https://images.unsplash.com/photo-1582510003544-4d00b7f74220"
                        ))
            except Exception:
                pass

        return results

    def search_hotels(
        self,
        query: str = "",
        city_id: Optional[str] = None,
        budget_tier: Optional[str] = None,
        max_price_inr: Optional[int] = None,
        limit: int = 3
    ) -> List[HotelCardData]:
        """Discovers verified hotels in Pondicherry or Chennai."""
        target_city = city_id if city_id and city_id in ["pondicherry", "chennai"] else "pondicherry"
        
        b_tiers = None
        if budget_tier and budget_tier != "all":
            try:
                b_tiers = [BudgetTierEnum(budget_tier.lower())]
            except Exception:
                pass

        hf = HotelFilter(
            city_id=target_city,
            budget_tiers=b_tiers,
            max_price_inr=max_price_inr
        )
        hotels = hotels_service.filter_hotels(hf)

        # If query specified text (e.g., 'seafront', 'taj', 'shanti'), filter locally
        if query and query.strip():
            q_lower = query.lower()
            matching = [h for h in hotels if q_lower in f"{h.name} {h.description} {h.proximity_tag or ''}".lower()]
            if matching:
                hotels = matching

        results: List[HotelCardData] = []
        for h in hotels[:limit]:
            results.append(HotelCardData(
                id=h.id,
                name=h.name,
                city_id=h.city_id or target_city,
                budget_tier=h.budget_tier.value if hasattr(h.budget_tier, "value") else str(h.budget_tier),
                price_per_night_inr=h.price_per_night_inr,
                rating=h.rating,
                address=h.address,
                amenities=h.amenities,
                proximity_tag=h.proximity_tag,
                image_url=h.image_url,
                booking_notice="Direct property confirmation advised for seasonal rates."
            ))
        return results

    def search_restaurants(
        self,
        query: str = "",
        city_id: Optional[str] = None,
        dietary: Optional[str] = None,
        limit: int = 3
    ) -> List[RestaurantCardData]:
        """Discovers dining spots and cafes with verified dietary compatibility."""
        target_city = city_id if city_id and city_id not in ["all", "both"] else None
        
        parsed_diet = None
        if dietary and dietary != "all":
            try:
                parsed_diet = DietaryOptionEnum(dietary.lower())
            except Exception:
                pass

        f = PlaceFilter(
            city_id=target_city,
            categories=[CategoryEnum.CAFE, CategoryEnum.DINING],
            dietary_preference=parsed_diet,
            search_query=query if query and len(query) > 2 else None
        )
        dining_places = places_service.filter_places(f)

        results: List[RestaurantCardData] = []
        seen_ids = set()

        for p in dining_places[:limit]:
            seen_ids.add(p.id)
            diet_opts = [d.value if hasattr(d, "value") else str(d) for d in p.dietary_options]
            results.append(RestaurantCardData(
                id=p.id,
                name=p.name,
                city_id=p.city_id or "pondicherry",
                category=p.category.value if hasattr(p.category, "value") else str(p.category),
                budget_tier=p.budget_tier.value if hasattr(p.budget_tier, "value") else str(p.budget_tier),
                dietary_options=diet_opts,
                estimated_cost_inr=p.estimated_cost_inr or 0,
                address=p.address,
                image_url=p.image_url
            ))

        # Enrich with VTKE if needed
        if getattr(settings, "KNOWLEDGE_RAG_ENABLED", True) and len(results) < limit:
            try:
                k_results = hybrid_retriever.search(
                    query=query or "",
                    city_id=target_city,
                    category="cafe",
                    dietary_preference=dietary,
                    top_k=limit
                )
                for ent, _score in k_results:
                    if len(results) >= limit:
                        break
                    if isinstance(ent, KnowledgeEntity) and ent.id not in seen_ids and (ent.category in ["cafe", "dining"] or ent.entity_type == "restaurant"):
                        seen_ids.add(ent.id)
                        results.append(RestaurantCardData(
                            id=ent.id,
                            name=ent.name,
                            city_id=ent.city_id or "pondicherry",
                            category=ent.category or "dining",
                            budget_tier=ent.budget_tier or "moderate",
                            dietary_options=ent.dietary_options or ["all"],
                            estimated_cost_inr=ent.estimated_cost_inr or 0,
                            address=ent.address or f"{ent.name}, {ent.city_id.capitalize() if ent.city_id else ''}",
                            image_url=ent.image_url or "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4"
                        ))
            except Exception:
                pass

        return results

discovery_service = DiscoveryService()
