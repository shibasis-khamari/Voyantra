"""
Voyantra Relevance & Provenance Reranker
Re-scores combined candidate entities based on base relevance, source authority,
verification status, and data freshness.
"""
from typing import List, Dict, Any, Tuple
from datetime import datetime, timezone
from ....schemas.knowledge import KnowledgeEntity, VerificationStatusEnum


class KnowledgeReranker:
    def __init__(self, authority_weight: float = 0.004, freshness_weight: float = 0.001):
        self.authority_weight = authority_weight
        self.freshness_weight = freshness_weight

    def rerank(
        self,
        query: str,
        candidates: List[Tuple[KnowledgeEntity, float]],
        top_k: int = 10,
    ) -> List[Tuple[KnowledgeEntity, float]]:
        """Reranks candidates combining base relevance with verified provenance and freshness."""
        if not candidates:
            return []

        q_lower = query.lower()
        q_tokens = set(q_lower.split())
        now_dt = datetime.now(timezone.utc)
        reranked: List[Tuple[KnowledgeEntity, float]] = []

        for ent, base_score in candidates:
            final_score = base_score

            # 1. Authority & Verification Boost (calibrated for RRF score range)
            if ent.verification_status == VerificationStatusEnum.VERIFIED:
                final_score += self.authority_weight
            elif ent.verification_status == VerificationStatusEnum.REVIEW_REQUIRED:
                final_score -= 0.002

            # 2. Source Authority Boost
            if ent.primary_source_id in ["official_tourism", "voyantra_catalog"]:
                final_score += 0.002

            # 3. Exact Name or Keyword Overlap Boost
            if ent.name.lower() in q_lower or q_lower in ent.name.lower():
                final_score += 0.015
            else:
                ent_text = f"{ent.name} {ent.description} {' '.join(ent.highlights)} {ent.category or ''}".lower()
                overlap = sum(1 for tok in q_tokens if tok in ent_text and len(tok) > 2)
                final_score += overlap * 0.003

            # 4. Freshness Boost
            if ent.updated_at:
                try:
                    up_dt = datetime.fromisoformat(ent.updated_at.replace("Z", "+00:00"))
                    days_old = (now_dt - up_dt).days
                    if days_old < 30:
                        final_score += self.freshness_weight
                    elif days_old > 365:
                        final_score -= 0.001
                except Exception:
                    pass

            reranked.append((ent, round(final_score, 6)))

        reranked.sort(key=lambda x: x[1], reverse=True)
        return reranked[:top_k]
