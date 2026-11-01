"""
Tests for Phase 6: Hybrid Retrieval Engine
Validates Structured Filters, Independent BM25, Geospatial Radius, Multilingual Vector,
Reciprocal Rank Fusion (RRF), Hard City Constraints, and Reranking.
"""
import pytest
from backend.app.schemas.knowledge import KnowledgeEntity, VerificationStatusEnum
from backend.app.services.knowledge.storage.knowledge_repository import KnowledgeRepository
from backend.app.services.knowledge.embeddings.embedding_service import EmbeddingService
from backend.app.services.knowledge.storage.vector_repository import LocalVectorRepository
from backend.app.services.knowledge.retrieval.structured_retriever import StructuredRetriever
from backend.app.services.knowledge.retrieval.keyword_retriever import BM25Retriever
from backend.app.services.knowledge.retrieval.geo_retriever import GeoRetriever
from backend.app.services.knowledge.retrieval.vector_retriever import VectorRetriever
from backend.app.services.knowledge.retrieval.hybrid_retriever import HybridRetriever
from backend.app.services.knowledge.retrieval.reranker import KnowledgeReranker


@pytest.fixture
def test_knowledge_env(tmp_path):
    repo = KnowledgeRepository(in_memory_only=True)
    vec_repo = LocalVectorRepository(storage_dir=str(tmp_path))
    embedder = EmbeddingService()

    # Seed diverse entities
    entities = [
        KnowledgeEntity(
            id="ent-pondy-promenade",
            city_id="pondicherry",
            name="Promenade Beach",
            category="beach",
            description="Scenic rock beach with colonial buildings along Goubert Avenue.",
            highlights=["French War Memorial", "Gandhi Statue"],
            budget_tier="budget",
            estimated_cost_inr=0,
            coordinates={"lat": 11.9338, "lng": 79.8358},
            verification_status=VerificationStatusEnum.VERIFIED,
            primary_source_id="official_tourism",
        ),
        KnowledgeEntity(
            id="ent-pondy-auroville",
            city_id="pondicherry",
            name="Auroville Matrimandir",
            category="spiritual",
            description="Peaceful meditation sphere and international community for human unity.",
            highlights=["Golden Sphere", "Peaceful Gardens", "Family Friendly"],
            budget_tier="budget",
            estimated_cost_inr=0,
            coordinates={"lat": 12.0069, "lng": 79.8106},
            verification_status=VerificationStatusEnum.VERIFIED,
            primary_source_id="official_tourism",
        ),
        KnowledgeEntity(
            id="ent-chennai-kapaleeshwarar",
            city_id="chennai",
            name="Kapaleeshwarar Temple",
            category="spiritual",
            description="Ancient 7th century Dravidian temple dedicated to Lord Shiva in Mylapore.",
            highlights=["Dravidian Architecture", "Temple Tank", "Sculptures"],
            budget_tier="budget",
            estimated_cost_inr=0,
            coordinates={"lat": 13.0336, "lng": 80.2697},
            verification_status=VerificationStatusEnum.VERIFIED,
            primary_source_id="official_tourism",
        ),
        KnowledgeEntity(
            id="ent-chennai-marina",
            city_id="chennai",
            name="Marina Beach",
            category="beach",
            description="Wide natural sandy beach along Bay of Bengal in Chennai.",
            highlights=["Lighthouse", "Seaside promenade", "Sunset walk"],
            budget_tier="budget",
            estimated_cost_inr=0,
            coordinates={"lat": 13.0500, "lng": 80.2824},
            verification_status=VerificationStatusEnum.VERIFIED,
            primary_source_id="official_tourism",
        ),
        KnowledgeEntity(
            id="ent-pondy-cafe-des-arts",
            city_id="pondicherry",
            name="Café des Arts",
            category="cafe",
            description="Bohemian French cafe serving baguettes, crepes, and coffee in White Town.",
            highlights=["Vintage Decor", "Garden Courtyard"],
            budget_tier="moderate",
            estimated_cost_inr=450,
            dietary_options=["vegetarian", "vegan"],
            coordinates={"lat": 11.9315, "lng": 79.8335},
            verification_status=VerificationStatusEnum.UNVERIFIED,
            primary_source_id="voyantra_catalog",
        ),
    ]

    for ent in entities:
        repo.upsert_entity(ent)
        # Also index into vector repository
        ent_text = f"{ent.name} {ent.description} {' '.join(ent.highlights)} {ent.category}"
        vec = embedder.embed_text(ent_text)
        vec_repo.add_vectors([{
            "id": f"vec-{ent.id}",
            "vector": vec,
            "metadata": {
                "entity_id": ent.id,
                "city_id": ent.city_id,
                "category": ent.category,
                "title": ent.name,
            }
        }])

    return repo, vec_repo, embedder


def test_structured_retriever_filtering(test_knowledge_env):
    repo, _, _ = test_knowledge_env
    retriever = StructuredRetriever(repository=repo)

    # Filter by dietary preference and category
    res = retriever.search(city_id="pondicherry", category="cafe", dietary_preference="vegan")
    assert len(res) == 1
    assert res[0].id == "ent-pondy-cafe-des-arts"

    # Filter by budget tier
    luxury = retriever.search(city_id="pondicherry", budget_tier="luxury")
    assert len(luxury) == 0


def test_bm25_lexical_retriever(test_knowledge_env):
    repo, _, _ = test_knowledge_env
    bm25 = BM25Retriever(repository=repo)

    # Search for French War Memorial
    matches = bm25.search("French War Memorial", city_id="pondicherry")
    assert len(matches) > 0
    top_ent, score = matches[0]
    assert top_ent.id == "ent-pondy-promenade"
    assert score > 0.0


def test_geo_retriever_radius(test_knowledge_env):
    repo, _, _ = test_knowledge_env
    geo = GeoRetriever(repository=repo)

    # Search within 2km of White Town (lat 11.9330, lng 79.8350)
    nearby = geo.search_radius(lat=11.9330, lng=79.8350, radius_km=2.0, city_id="pondicherry")
    assert len(nearby) >= 2
    ids = [e.id for e, d in nearby]
    assert "ent-pondy-promenade" in ids
    assert "ent-pondy-cafe-des-arts" in ids
    # Auroville is ~10km away, should NOT be in 2km radius
    assert "ent-pondy-auroville" not in ids


def test_multilingual_vector_retriever(test_knowledge_env):
    repo, vec_repo, embedder = test_knowledge_env
    vec_retriever = VectorRetriever(embedder=embedder, vector_repo=vec_repo, knowledge_repo=repo)

    # Hindi query for peaceful family spot
    hi_results = vec_retriever.search("शांत और परिवार के साथ घूमने के लिए जगह", city_id="pondicherry")
    assert len(hi_results) > 0
    top_hi, score_hi = hi_results[0]
    assert top_hi.id == "ent-pondy-auroville"

    # Tamil query for temple / spiritual in Chennai
    ta_results = vec_retriever.search("கோவில் ஆன்மீக தலம்", city_id="chennai")
    assert len(ta_results) > 0
    top_ta, score_ta = ta_results[0]
    assert top_ta.id == "ent-chennai-kapaleeshwarar"


def test_hybrid_retriever_rrf_fusion(test_knowledge_env):
    repo, vec_repo, embedder = test_knowledge_env
    hybrid = HybridRetriever(repository=repo)
    hybrid.vector = VectorRetriever(embedder=embedder, vector_repo=vec_repo, knowledge_repo=repo)

    fused = hybrid.search(query="french cafe coffee and baguettes", city_id="pondicherry")
    assert len(fused) > 0
    top_ent, score = fused[0]
    assert top_ent.id == "ent-pondy-cafe-des-arts"


def test_hybrid_retriever_city_hard_constraint(test_knowledge_env):
    repo, vec_repo, embedder = test_knowledge_env
    hybrid = HybridRetriever(repository=repo)
    hybrid.vector = VectorRetriever(embedder=embedder, vector_repo=vec_repo, knowledge_repo=repo)

    # Searching for beach in Pondicherry MUST NOT return Marina Beach (Chennai)
    pondy_beaches = hybrid.search(query="sandy beach seaside walk", city_id="pondicherry")
    for ent, _ in pondy_beaches:
        assert ent.city_id == "pondicherry"
        assert ent.name != "Marina Beach"


def test_reranker_provenance_boost():
    reranker = KnowledgeReranker(authority_weight=0.20)
    
    verified_ent = KnowledgeEntity(
        id="ent-1",
        name="Official Monument",
        verification_status=VerificationStatusEnum.VERIFIED,
        primary_source_id="official_tourism",
    )
    unverified_ent = KnowledgeEntity(
        id="ent-2",
        name="Unverified Spot",
        verification_status=VerificationStatusEnum.UNVERIFIED,
        primary_source_id="osm",
    )
    
    # Both start with same base score
    candidates = [(unverified_ent, 0.50), (verified_ent, 0.50)]
    ranked = reranker.rerank(query="monument", candidates=candidates)
    
    assert ranked[0][0].id == "ent-1"
    assert ranked[0][1] > ranked[1][1]
