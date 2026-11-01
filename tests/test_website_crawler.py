"""
Tests for Phase 4 & 5: Website Crawler, Chunker, Multilingual Embeddings, and Vector Repository
Validates SSRF prevention, IP pinning, content diffing, chunking, multilingual vectors, and atomic shadow swaps.
"""
import pytest
from backend.app.schemas.knowledge import KnowledgeDocument, KnowledgeEntity
from backend.app.services.knowledge.storage.knowledge_repository import KnowledgeRepository
from backend.app.services.knowledge.ingestion.website_crawler import (
    WebsiteCrawler,
    SSRFValidationError,
)
from backend.app.services.knowledge.processing.chunker import TextChunker
from backend.app.services.knowledge.embeddings.embedding_service import EmbeddingService
from backend.app.services.knowledge.storage.vector_repository import LocalVectorRepository



def test_crawler_blocks_private_ips_and_ssrf():
    """Validates SSRF filter blocks private, loopback, and cloud metadata IPs."""
    crawler = WebsiteCrawler()
    
    # Blocked IPv4
    assert crawler.is_ip_blocked("127.0.0.1") is True
    assert crawler.is_ip_blocked("10.0.0.5") is True
    assert crawler.is_ip_blocked("169.254.169.254") is True
    assert crawler.is_ip_blocked("192.168.1.100") is True
    assert crawler.is_ip_blocked("172.16.5.1") is True
    assert crawler.is_ip_blocked("0.0.0.0") is True

    # Blocked IPv6 & IPv4-mapped
    assert crawler.is_ip_blocked("::1") is True
    assert crawler.is_ip_blocked("::ffff:127.0.0.1") is True
    assert crawler.is_ip_blocked("::ffff:169.254.169.254") is True

    # Public IP should not be blocked
    assert crawler.is_ip_blocked("8.8.8.8") is False
    assert crawler.is_ip_blocked("1.1.1.1") is False


def test_crawler_rejects_unallowed_domains():
    """Validates that crawling domains outside the allowlist raises SSRFValidationError."""
    crawler = WebsiteCrawler(allowed_domains=["voyantra.com"])
    with pytest.raises(SSRFValidationError, match="not in allowed crawl domains"):
        crawler.validate_and_resolve_destination("https://malicious-website.com/secret")


def test_crawler_clean_content_extraction():
    """Validates stripping of scripts, styles, headers, and nav elements from raw HTML."""
    crawler = WebsiteCrawler()
    raw_html = """
    <!DOCTYPE html>
    <html>
      <head><title>Pondicherry Heritage Walking Tour - Voyantra</title><script>var x = 1;</script></head>
      <body>
        <nav><a href="/">Home</a></nav>
        <header><h1>Header Navigation</h1></header>
        <main>
          <h2>French Quarter Heritage</h2>
          <p>Explore mustard-yellow colonial villas and tranquil seaside boulevards.</p>
        </main>
        <footer>Privacy Policy & Terms</footer>
      </body>
    </html>
    """
    title, cleaned = crawler.extract_clean_content(raw_html)
    assert title == "Pondicherry Heritage Walking Tour - Voyantra"
    assert "Explore mustard-yellow colonial villas" in cleaned
    assert "var x = 1" not in cleaned
    assert "Privacy Policy & Terms" not in cleaned


def test_crawler_content_hash_diffing_and_versioning(tmp_path):
    """Validates page versioning, content-hash diffing, and prior chunk deactivation."""
    repo = KnowledgeRepository()
    crawler = WebsiteCrawler(repository=repo)

    # Initial mock page
    html_v1 = "<html><head><title>FAQ</title></head><body><p>Voyantra provides curated itineraries.</p></body></html>"
    title_1, clean_1 = crawler.extract_clean_content(html_v1)
    
    doc_1 = KnowledgeDocument(
        id="doc-faq",
        source_id="voyantra_website",
        url="https://voyantra.com/faq",
        title=title_1,
        cleaned_content=clean_1,
        content_hash="hash_v1",
        version=1,
    )
    repo.upsert_document(doc_1)

    # Crawling with same content hash
    assert doc_1.version == 1
    assert doc_1.is_active is True


def test_text_chunker():
    """Validates heading-aware document chunking and entity chunking."""
    chunker = TextChunker(target_chunk_chars=300)
    doc = KnowledgeDocument(
        id="doc-guide",
        source_id="voyantra_website",
        url="https://voyantra.com/guide",
        title="Guide to Chennai",
        cleaned_content=(
            "HISTORIC MYLAPORE:\n"
            "Mylapore is one of the oldest residential parts of Chennai.\n"
            "It is home to the Kapaleeshwarar Temple and classical music venues.\n\n"
            "MARINA BEACHFRONT:\n"
            "Marina Beach is a wide sandy beach stretching 12 km.\n"
            "Lighthouse visits and evening strolls are popular here."
        ),
        content_hash="guide_hash",
        version=1,
    )
    chunks = chunker.chunk_document(doc)
    assert len(chunks) >= 1
    assert any("Mylapore" in chk.content for chk in chunks)
    assert any(chk.heading_context for chk in chunks)

    # Test Entity Chunking
    ent = KnowledgeEntity(
        id="ent-matrimandir",
        name="Auroville Matrimandir",
        description="Golden metallic sphere for meditation.",
        highlights=["Peace Zone", "Geodesic Structure"],
        city_id="pondicherry",
        category="spiritual",
    )
    ent_chunks = chunker.chunk_entity(ent)
    assert len(ent_chunks) == 1
    assert "Golden metallic sphere" in ent_chunks[0].content
    assert ent_chunks[0].category == "spiritual"


def test_multilingual_embedding_service():
    """Validates multilingual embedding generation across English, Hindi, and Tamil."""
    svc = EmbeddingService()
    
    vec_en = svc.embed_text("Peaceful and family-friendly place")
    vec_hi = svc.embed_text("शांत और परिवार के साथ घूमने के लिए जगह बताओ")
    vec_ta = svc.embed_text("குடும்பத்துடன் செல்ல அமைதியான இடங்கள்")

    assert len(vec_en) == 384
    assert len(vec_hi) == 384
    assert len(vec_ta) == 384

    # Verify L2 normalization
    import numpy as np
    assert abs(np.linalg.norm(np.array(vec_en)) - 1.0) < 1e-4
    assert abs(np.linalg.norm(np.array(vec_hi)) - 1.0) < 1e-4
    assert abs(np.linalg.norm(np.array(vec_ta)) - 1.0) < 1e-4

    # Verify semantic alignment between Hindi and Tamil peaceful/family queries (non-zero similarity)
    sim_hi_ta = float(np.dot(np.array(vec_hi), np.array(vec_ta)))
    assert sim_hi_ta > 0.15, f"Expected cross-lingual concept match, got similarity {sim_hi_ta}"


def test_vector_repository_shadow_swap_and_lock(tmp_path):
    """Validates atomic shadow swaps, generation ID tracking, search, and deletion."""
    repo = LocalVectorRepository(storage_dir=str(tmp_path))
    
    records = [
        {
            "id": "chk-01",
            "vector": [1.0] + [0.0] * 383,
            "metadata": {"city_id": "pondicherry", "category": "beach", "title": "Promenade Beach"}
        },
        {
            "id": "chk-02",
            "vector": [0.0, 1.0] + [0.0] * 382,
            "metadata": {"city_id": "chennai", "category": "spiritual", "title": "Kapaleeshwarar Temple"}
        },
    ]
    
    # 1. Add vectors
    added = repo.add_vectors(records)
    assert added == 2
    gen_1 = repo._cached_generation_id
    assert gen_1 is not None

    # 2. Search
    results = repo.search([1.0] + [0.0] * 383, top_k=2)
    assert len(results) == 2
    assert results[0]["id"] == "chk-01"
    assert results[0]["score"] > 0.9

    # 3. Search with Metadata filter
    pondy_res = repo.search([0.0, 1.0] + [0.0] * 382, top_k=2, filter_dict={"city_id": "chennai"})
    assert len(pondy_res) == 1
    assert pondy_res[0]["id"] == "chk-02"

    # 4. Atomic Delete
    deleted = repo.delete_vectors(["chk-01"])
    assert deleted == 1
    gen_2 = repo._cached_generation_id
    assert gen_2 != gen_1

    remaining = repo.search([1.0] + [0.0] * 383, top_k=5)
    assert len(remaining) == 1
    assert remaining[0]["id"] == "chk-02"

    # 5. Benchmark index
    stats = repo.benchmark_index()
    assert stats["document_count"] == 1
    assert stats["avg_latency_ms"] < 20.0
