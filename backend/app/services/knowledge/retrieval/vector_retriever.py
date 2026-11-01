"""
Voyantra Multilingual Vector Retriever
Performs cosine semantic similarity searches using the multilingual embedding service
and the process-safe vector repository.
"""
from typing import List, Tuple, Dict, Any, Optional
from ....schemas.knowledge import KnowledgeEntity, KnowledgeChunk
from ..embeddings.embedding_service import EmbeddingService, embedding_service
from ..storage.vector_repository import LocalVectorRepository, vector_repository
from ..storage.knowledge_repository import KnowledgeRepository, knowledge_repository


class VectorRetriever:
    def __init__(
        self,
        embedder: Optional[EmbeddingService] = None,
        vector_repo: Optional[LocalVectorRepository] = None,
        knowledge_repo: Optional[KnowledgeRepository] = None,
    ):
        self.embedder = embedder or embedding_service
        self.vector_repo = vector_repo or vector_repository
        self.knowledge_repo = knowledge_repo or knowledge_repository

    def search(
        self,
        query: str,
        city_id: Optional[str] = None,
        category: Optional[str] = None,
        top_k: int = 10,
    ) -> List[Tuple[Any, float]]:
        """
        Embeds user query and searches the vector index.
        Returns list of (KnowledgeEntity or KnowledgeChunk or Metadata dict, score).
        """
        q_vec = self.embedder.embed_text(query)
        filter_dict: Dict[str, Any] = {}
        if city_id:
            filter_dict["city_id"] = city_id.lower()
        if category:
            filter_dict["category"] = category.lower()

        raw_results = self.vector_repo.search(
            query_vector=q_vec,
            top_k=top_k,
            filter_dict=filter_dict if filter_dict else None,
        )

        resolved_results: List[Tuple[Any, float]] = []
        for r in raw_results:
            meta = r.get("metadata", {})
            ent_id = meta.get("entity_id")
            doc_id = meta.get("document_id")

            if ent_id:
                ent = self.knowledge_repo.get_entity(ent_id)
                if ent:
                    resolved_results.append((ent, r["score"]))
                    continue

            if doc_id:
                chunk = self.knowledge_repo.get_chunk(r["id"])
                if chunk:
                    resolved_results.append((chunk, r["score"]))
                    continue

            # Fallback to metadata dict
            resolved_results.append((meta, r["score"]))

        return resolved_results
