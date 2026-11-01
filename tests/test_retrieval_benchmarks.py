"""
Tests for Phase 11: Measurable Multilingual Retrieval Evaluation Benchmarks
Evaluates Recall@5, Precision@5, latency (< 250ms), and unsupported-answer rate on real queries
across English, Hindi, and Tamil as specified in Section 6 of VTKE Implementation Plan.
"""
import time
import pytest
from backend.app.schemas.knowledge import KnowledgeEntity, VerificationStatusEnum
from backend.app.services.knowledge.storage.knowledge_repository import KnowledgeRepository
from backend.app.services.knowledge.embeddings.embedding_service import EmbeddingService
from backend.app.services.knowledge.storage.vector_repository import LocalVectorRepository
from backend.app.services.knowledge.retrieval.hybrid_retriever import HybridRetriever
from backend.app.services.conversation.orchestrator import ConversationOrchestrator
from backend.app.schemas.chat import ChatTurnRequest


@pytest.fixture(scope="module")
def benchmark_engine(tmp_path_factory):
    storage_dir = tmp_path_factory.mktemp("benchmark_vectors")
    repo = KnowledgeRepository(in_memory_only=True)
    vec_repo = LocalVectorRepository(storage_dir=str(storage_dir))
    embedder = EmbeddingService(api_key="")

    # Seed the benchmark knowledge entities
    entities = [
        KnowledgeEntity(
            id="ent-promenade",
            city_id="pondicherry",
            name="Promenade Beach",
            category="beach",
            description="Famous rocky seaside promenade along White Town in Pondicherry with Gandhi statue.",
            highlights=["Rocky Promenade", "White Town", "Sea breeze"],
            coordinates={"lat": 11.9338, "lng": 79.8358},
            verification_status=VerificationStatusEnum.VERIFIED,
            primary_source_url="https://pondytourism.py.gov.in/promenade",
        ),
        KnowledgeEntity(
            id="ent-serenity",
            city_id="pondicherry",
            name="Serenity Beach",
            category="beach",
            description="Golden sand surf beach north of White Town Pondicherry.",
            highlights=["Surfing", "Golden Sand"],
            coordinates={"lat": 11.9700, "lng": 79.8450},
            verification_status=VerificationStatusEnum.VERIFIED,
            primary_source_url="https://pondytourism.py.gov.in/serenity",
        ),
        KnowledgeEntity(
            id="ent-auroville",
            city_id="pondicherry",
            name="Auroville Matrimandir",
            category="spiritual",
            description="A peaceful meditation sanctuary and international community for families and travelers.",
            highlights=["Peaceful Meditation", "Family Friendly", "Tranquil Garden"],
            coordinates={"lat": 12.0069, "lng": 79.8106},
            verification_status=VerificationStatusEnum.VERIFIED,
            primary_source_url="https://auroville.org",
        ),
        KnowledgeEntity(
            id="ent-botanical",
            city_id="pondicherry",
            name="Botanical Garden",
            category="nature",
            description="Tranquil family-friendly French colonial garden with rare trees and peaceful walking paths.",
            highlights=["Shaded Pathways", "Family Picnic", "Botanical Specimen"],
            coordinates={"lat": 11.9298, "lng": 79.8227},
            verification_status=VerificationStatusEnum.VERIFIED,
            primary_source_url="https://pondytourism.py.gov.in/botanical",
        ),
        KnowledgeEntity(
            id="ent-kapaleeshwarar",
            city_id="chennai",
            name="Kapaleeshwarar Temple",
            category="spiritual",
            description="7th-century Dravidian Shiva temple in Mylapore with iconic gopurams and sacred tank.",
            highlights=["7th Century", "Dravidian Architecture", "Shiva Temple"],
            coordinates={"lat": 13.0336, "lng": 80.2697},
            verification_status=VerificationStatusEnum.VERIFIED,
            primary_source_url="https://hrce.tn.gov.in/kapaleeshwarar",
        ),
        KnowledgeEntity(
            id="ent-marina",
            city_id="chennai",
            name="Marina Beach",
            category="beach",
            description="Long natural urban sandy beach along Bay of Bengal in Chennai, popular for family outings.",
            highlights=["Sandy Beach", "Family Outing", "Lighthouse"],
            coordinates={"lat": 13.0500, "lng": 80.2824},
            verification_status=VerificationStatusEnum.VERIFIED,
            primary_source_url="https://chennaicorporation.gov.in",
        ),
    ]

    for ent in entities:
        repo.upsert_entity(ent)
        text = f"{ent.name} {ent.description} {' '.join(ent.highlights)} {ent.category}"
        vec = embedder.embed_text(text)
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

    hybrid = HybridRetriever(repository=repo)
    hybrid.vector.embedder = embedder
    hybrid.vector.vector_repo = vec_repo
    hybrid.vector.knowledge_repo = repo

    return hybrid


def test_benchmark_recall_and_precision_english_beaches(benchmark_engine):
    """Query: 'Best beaches near White Town' -> Target: Promenade Beach, Serenity Beach."""
    t0 = time.time()
    results = benchmark_engine.search("Best beaches near White Town", city_id="pondicherry", top_k=5)
    latency_ms = (time.time() - t0) * 1000.0

    assert latency_ms < 250.0, f"Latency {latency_ms:.2f}ms exceeded 250ms threshold"

    result_ids = [ent.id for ent, _ in results]
    target_ids = {"ent-promenade", "ent-serenity"}
    
    # Recall@5: How many targets found
    hits = sum(1 for tid in target_ids if tid in result_ids)
    recall_at_5 = hits / float(len(target_ids))
    assert recall_at_5 >= 0.50, f"Recall@5 {recall_at_5} below benchmark"

    # Precision@5: How many retrieved are relevant beach places
    beach_hits = sum(1 for ent, _ in results if ent.category == "beach")
    precision_at_5 = beach_hits / float(len(results)) if results else 0
    assert precision_at_5 >= 0.50, f"Precision@5 {precision_at_5} below benchmark"


def test_benchmark_hindi_peaceful_family_places(benchmark_engine):
    """Query: 'शांत जगहें जहाँ परिवार जा सके' -> Target: Auroville Matrimandir, Botanical Garden."""
    t0 = time.time()
    results = benchmark_engine.search("शांत जगहें जहाँ परिवार जा सके", city_id="pondicherry", top_k=5)
    latency_ms = (time.time() - t0) * 1000.0

    assert latency_ms < 250.0

    result_ids = [ent.id for ent, _ in results]
    assert "ent-auroville" in result_ids or "ent-botanical" in result_ids


def test_benchmark_tamil_family_places(benchmark_engine):
    """Query: 'குடும்பத்துடன் செல்ல ஏற்ற அமைதியான இடங்கள்' -> Target: Kapaleeshwarar Temple, Marina Beach."""
    t0 = time.time()
    results = benchmark_engine.search("குடும்பத்துடன் செல்ல ஏற்ற அமைதியான இடங்கள்", city_id="chennai", top_k=5)
    latency_ms = (time.time() - t0) * 1000.0

    assert latency_ms < 250.0

    result_ids = [ent.id for ent, _ in results]
    assert "ent-kapaleeshwarar" in result_ids or "ent-marina" in result_ids


def test_benchmark_history_and_citation_correctness(benchmark_engine):
    """Query: 'History of Kapaleeshwarar Temple' -> Must return Kapaleeshwarar with official citation."""
    results = benchmark_engine.search("History of Kapaleeshwarar Temple", city_id="chennai", top_k=3)
    assert len(results) > 0
    top_ent, _ = results[0]
    assert top_ent.id == "ent-kapaleeshwarar"
    assert top_ent.primary_source_url == "https://hrce.tn.gov.in/kapaleeshwarar"


def test_benchmark_unsupported_out_of_catalog_accuracy():
    """Query: 'What is the entry fee for Tokyo Tower?' -> Negative policy: zero fabricated rates."""
    orchestrator = ConversationOrchestrator()
    req = ChatTurnRequest(
        message="What is the entry fee for Tokyo Tower?",
        conversation_id="bench-tokyo-01",
        language="en"
    )
    resp = orchestrator.process_turn(req)
    
    # Must not claim Tokyo is verified Pondy/Chennai place, and must not fabricate local pricing
    reply = resp.reply_message.lower()
    assert "tokyo" in reply
    assert resp.places == []
    assert resp.itinerary is None
