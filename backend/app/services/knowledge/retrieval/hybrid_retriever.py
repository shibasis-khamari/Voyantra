"""
Voyantra Hybrid Retrieval Engine
Executes multi-channel retrieval (Structured, BM25 Lexical, Geospatial Radius, Multilingual Vector)
and fuses results using Reciprocal Rank Fusion (RRF) with strict city constraint filtering.
"""
from typing import List, Dict, Any, Optional, Tuple
from ....schemas.knowledge import KnowledgeEntity
from ..storage.knowledge_repository import KnowledgeRepository, knowledge_repository
from .structured_retriever import StructuredRetriever
from .keyword_retriever import BM25Retriever
from .geo_retriever import GeoRetriever
from .vector_retriever import VectorRetriever
from .reranker import KnowledgeReranker


class HybridRetriever:
    def __init__(
        self,
        repository: Optional[KnowledgeRepository] = None,
        rrf_k: int = 60,
    ):
        self.repo = repository or knowledge_repository
        self.rrf_k = rrf_k
        self.structured = StructuredRetriever(self.repo)
        self.bm25 = BM25Retriever(self.repo)
        self.geo = GeoRetriever(self.repo)
        self.vector = VectorRetriever(knowledge_repo=self.repo)
        self.reranker = KnowledgeReranker()

    def search(
        self,
        query: str,
        city_id: Optional[str] = None,
        category: Optional[str] = None,
        budget_tier: Optional[str] = None,
        max_cost_inr: Optional[int] = None,
        dietary_preference: Optional[str] = None,
        near_lat: Optional[float] = None,
        near_lng: Optional[float] = None,
        radius_km: float = 8.0,
        top_k: int = 10,
    ) -> List[Tuple[KnowledgeEntity, float]]:
        """
        Executes hybrid retrieval across all channels and fuses scores using RRF.
        Strictly enforces city_id constraint when specified.
        """
        target_city = city_id.lower() if city_id and city_id not in ["all", "both"] else None
        target_category = category.lower() if category and category != "all" else None

        rrf_scores: Dict[str, float] = {}
        entity_cache: Dict[str, KnowledgeEntity] = {}

        # Channel 1: Structured Constraints (only if structured filters are specified)
        has_structured_filters = bool(
            target_category or budget_tier or max_cost_inr is not None or dietary_preference
        )
        if has_structured_filters:
            struct_results = self.structured.search(
                city_id=target_city,
                category=target_category,
                budget_tier=budget_tier,
                max_cost_inr=max_cost_inr,
                dietary_preference=dietary_preference,
                limit=30,
            )
            for rank, ent in enumerate(struct_results, start=1):
                entity_cache[ent.id] = ent
                rrf_scores[ent.id] = rrf_scores.get(ent.id, 0.0) + (0.8 / (self.rrf_k + rank))

        # Channel 2: Lexical BM25 Search
        if query and query.strip():
            bm25_results = self.bm25.search(query=query, city_id=target_city, top_k=25)
            for rank, (ent, _score) in enumerate(bm25_results, start=1):
                entity_cache[ent.id] = ent
                rrf_scores[ent.id] = rrf_scores.get(ent.id, 0.0) + (1.0 / (self.rrf_k + rank))

        # Channel 3: Multilingual Vector Search
        if query and query.strip():
            vector_results = self.vector.search(
                query=query,
                city_id=target_city,
                category=target_category,
                top_k=25,
            )
            for rank, (item, _score) in enumerate(vector_results, start=1):
                if isinstance(item, KnowledgeEntity):
                    entity_cache[item.id] = item
                    rrf_scores[item.id] = rrf_scores.get(item.id, 0.0) + (1.2 / (self.rrf_k + rank))

        # Channel 4: Geospatial Radius Search
        if near_lat is not None and near_lng is not None:
            geo_results = self.geo.search_radius(
                lat=near_lat,
                lng=near_lng,
                radius_km=radius_km,
                city_id=target_city,
                category=target_category,
                top_k=20,
            )
            for rank, (ent, _dist) in enumerate(geo_results, start=1):
                entity_cache[ent.id] = ent
                rrf_scores[ent.id] = rrf_scores.get(ent.id, 0.0) + (1.0 / (self.rrf_k + rank))

        if not rrf_scores:
            # Fallback to general city places if query returned 0 matches
            fallback_entities = self.repo.find_entities(city_id=target_city, category=target_category, limit=top_k)
            return [(e, 0.5) for e in fallback_entities]

        # Filter strictly by city_id if specified
        valid_candidates: List[Tuple[KnowledgeEntity, float]] = []
        for ent_id, score in rrf_scores.items():
            ent = entity_cache.get(ent_id)
            if not ent:
                continue
            if target_city and ent.city_id and ent.city_id.lower() != target_city:
                continue  # Hard city constraint violated
            valid_candidates.append((ent, score))

        # Apply reranking
        final_results = self.reranker.rerank(
            query=query or "",
            candidates=valid_candidates,
            top_k=top_k,
        )
        return final_results


hybrid_retriever = HybridRetriever()
