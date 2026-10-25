import math
from typing import List, Tuple
from ..schemas.place import Place
from .places_service import places_service

class VectorStoreService:
    def __init__(self):
        self._model = None
        self._initialized = False

    def _init_model(self):
        if self._initialized:
            return
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer('all-MiniLM-L6-v2')
            print("[VectorStore] SentenceTransformers all-MiniLM-L6-v2 loaded successfully.")
        except Exception as e:
            print(f"[VectorStore] SentenceTransformers not loaded ({e}), using fallback semantic vector matcher.")
        self._initialized = True

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    def search_semantic_places(self, query_text: str, city_id: str = "pondicherry", top_k: int = 8) -> List[Tuple[Place, float]]:
        self._init_model()
        places = places_service.get_all_places(city_id)
        if not places:
            return []

        if self._model:
            try:
                # 1. Embed query
                query_vec = self._model.encode(query_text).tolist()
                
                # 2. Embed place texts
                place_texts = [f"{p.name} {p.category.value} {p.sub_category or ''} {p.description} {' '.join(p.tags)}" for p in places]
                place_vecs = self._model.encode(place_texts).tolist()

                scored = []
                for p, v in zip(places, place_vecs):
                    sim = self._cosine_similarity(query_vec, v)
                    score = round(sim * 100, 1)
                    scored.append((p, score))

                scored.sort(key=lambda x: x[1], reverse=True)
                return scored[:top_k]
            except Exception as e:
                print(f"[VectorStore] SentenceTransformers search failed: {e}")

        # Fallback Word Frequency Vector Matcher
        q_words = set(query_text.lower().split())
        scored = []
        for p in places:
            text = f"{p.name} {p.category.value} {p.sub_category or ''} {p.description} {' '.join(p.tags)}".lower()
            matches = sum(1 for w in q_words if w in text and len(w) > 2)
            score = min(98.0, 45.0 + (matches * 15.0))
            scored.append((p, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

vector_store_service = VectorStoreService()
