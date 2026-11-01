"""
Voyantra Structured Retriever
Applies deterministic hard constraints (city_id, category, budget_tier, verification_status).
"""
from typing import List, Optional, Dict, Any
from ....schemas.knowledge import KnowledgeEntity
from ..storage.knowledge_repository import KnowledgeRepository, knowledge_repository


class StructuredRetriever:
    def __init__(self, repository: Optional[KnowledgeRepository] = None):
        self.repo = repository or knowledge_repository

    def search(
        self,
        city_id: Optional[str] = None,
        category: Optional[str] = None,
        budget_tier: Optional[str] = None,
        max_cost_inr: Optional[int] = None,
        dietary_preference: Optional[str] = None,
        verification_status: Optional[str] = None,
        entity_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[KnowledgeEntity]:
        """Finds entities matching all provided hard constraints."""
        all_candidates = self.repo.find_entities(
            city_id=city_id,
            entity_type=entity_type,
            category=category,
            verification_status=verification_status,
            limit=limit * 2,
        )

        matched: List[KnowledgeEntity] = []
        for ent in all_candidates:
            if budget_tier:
                if not ent.budget_tier or ent.budget_tier.lower() != budget_tier.lower():
                    continue
            if max_cost_inr is not None:
                if ent.estimated_cost_inr is not None and ent.estimated_cost_inr > max_cost_inr:
                    continue
            if dietary_preference and dietary_preference != "all":
                d_lower = dietary_preference.lower()
                ent_diets = [d.lower() for d in ent.dietary_options]
                if d_lower not in ent_diets and "all" not in ent_diets:
                    continue
            matched.append(ent)
            if len(matched) >= limit:
                break

        return matched
