"""
Voyantra Independent Lexical Keyword Retriever (BM25)
Implements true Okapi BM25 scoring over knowledge entity textual fields.
Strictly lexical token matching - never mixed into vector embeddings.
"""
import math
import re
from typing import List, Dict, Any, Optional, Tuple
from ....schemas.knowledge import KnowledgeEntity
from ..storage.knowledge_repository import KnowledgeRepository, knowledge_repository


def tokenize(text: str) -> List[str]:
    """Tokenizes text into lowercase alphanumeric words."""
    if not text:
        return []
    clean = re.sub(r"[^\w\s]", " ", text.lower())
    return [w for w in clean.split() if len(w) > 1]


class BM25Retriever:
    def __init__(
        self,
        repository: Optional[KnowledgeRepository] = None,
        k1: float = 1.5,
        b: float = 0.75
    ):
        self.repo = repository or knowledge_repository
        self.k1 = k1
        self.b = b

    def _build_corpus(self, city_id: Optional[str] = None) -> Tuple[List[KnowledgeEntity], List[List[str]], Dict[str, int], float]:
        entities = self.repo.find_entities(city_id=city_id, limit=500)
        corpus_tokens: List[List[str]] = []
        df: Dict[str, int] = {}
        total_len = 0

        for ent in entities:
            # Build unified document text from all descriptive fields
            doc_text = f"{ent.name} {' '.join(ent.alternate_names)} {ent.description} {' '.join(ent.highlights)} {' '.join(ent.tags)} {ent.category or ''} {ent.sub_category or ''}"
            tokens = tokenize(doc_text)
            corpus_tokens.append(tokens)
            total_len += len(tokens)
            
            # Document frequency
            unique_terms = set(tokens)
            for t in unique_terms:
                df[t] = df.get(t, 0) + 1

        n_docs = len(entities)
        avgdl = (total_len / n_docs) if n_docs > 0 else 1.0
        return entities, corpus_tokens, df, avgdl

    def search(
        self,
        query: str,
        city_id: Optional[str] = None,
        top_k: int = 10,
    ) -> List[Tuple[KnowledgeEntity, float]]:
        """Scores entities using Okapi BM25 ranking."""
        q_tokens = tokenize(query)
        if not q_tokens:
            return []

        entities, corpus_tokens, df, avgdl = self._build_corpus(city_id=city_id)
        n_docs = len(entities)
        if n_docs == 0:
            return []

        scored_results: List[Tuple[KnowledgeEntity, float]] = []

        for idx, ent in enumerate(entities):
            doc_tokens = corpus_tokens[idx]
            doc_len = len(doc_tokens)
            if doc_len == 0:
                continue

            # Term frequencies in this document
            tf: Dict[str, int] = {}
            for t in doc_tokens:
                tf[t] = tf.get(t, 0) + 1

            doc_score = 0.0
            for term in q_tokens:
                if term not in tf:
                    continue
                # Term frequency in document
                freq = tf[term]
                # Document frequency across corpus
                doc_freq = df.get(term, 0)
                # BM25 IDF with smoothing
                idf = math.log(1.0 + (n_docs - doc_freq + 0.5) / (doc_freq + 0.5))
                # BM25 TF component
                tf_component = (freq * (self.k1 + 1.0)) / (freq + self.k1 * (1.0 - self.b + self.b * (doc_len / avgdl)))
                doc_score += idf * tf_component

            if doc_score > 0.0:
                scored_results.append((ent, doc_score))

        # Sort descending by BM25 score
        scored_results.sort(key=lambda x: x[1], reverse=True)
        return scored_results[:top_k]
