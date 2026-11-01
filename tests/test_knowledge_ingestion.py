"""
Tests for Phase 2 & 3: Ingestion Adapters, Multi-Signal Resolution, and Validation
Validates Wikidata, OSM, Wikipedia, Tourism adapters, normalizer, deduplicator thresholds, and validator fallbacks.
"""
import pytest
from backend.app.schemas.knowledge import (
    KnowledgeEntity,
    VerificationStatusEnum,
    PriceStatusEnum,
)
from backend.app.services.knowledge.storage.knowledge_repository import KnowledgeRepository
from backend.app.services.knowledge.ingestion.wikidata_adapter import WikidataAdapter
from backend.app.services.knowledge.ingestion.osm_adapter import OSMAdapter
from backend.app.services.knowledge.ingestion.wikipedia_adapter import WikipediaAdapter
from backend.app.services.knowledge.ingestion.tourism_adapter import TourismAdapter
from backend.app.services.knowledge.processing.normalizer import EntityNormalizer
from backend.app.services.knowledge.processing.deduplicator import EntityDeduplicator
from backend.app.services.knowledge.processing.validator import EntityValidator
from backend.app.services.knowledge.ingestion_manager import IngestionManager


def test_wikidata_adapter_records():
    """Validates Wikidata ingestion and entity transformation with CC0 attribution."""
    adapter = WikidataAdapter()
    records = adapter.fetch_raw_records("pondicherry", limit=5)
    assert len(records) > 0
    
    first = records[0]
    entity = adapter.transform_to_entity(first, city_id="pondicherry")
    
    assert entity.city_id == "pondicherry"
    assert entity.entity_type == "place"
    assert "wikidata" in entity.primary_source_id
    assert "CC0" in entity.license
    assert entity.verification_status == VerificationStatusEnum.UNVERIFIED
    assert entity.price_status == PriceStatusEnum.UNKNOWN
    assert entity.coordinates is not None


def test_osm_adapter_records():
    """Validates OpenStreetMap Overpass ingestion with ODbL attribution."""
    adapter = OSMAdapter()
    records = adapter.fetch_raw_records("chennai", limit=5)
    assert len(records) > 0
    
    entity = adapter.transform_to_entity(records[0], city_id="chennai")
    assert entity.city_id == "chennai"
    assert "osm" in entity.primary_source_id
    assert "ODbL" in entity.license
    assert entity.verification_status == VerificationStatusEnum.UNVERIFIED


def test_wikipedia_adapter_records():
    """Validates Wikipedia encyclopedic extracts and CC BY-SA 4.0 license."""
    adapter = WikipediaAdapter()
    records = adapter.fetch_raw_records("pondicherry", limit=3)
    assert len(records) > 0
    
    entity = adapter.transform_to_entity(records[0], city_id="pondicherry")
    assert "wikipedia" in entity.primary_source_id
    assert "CC BY-SA 4.0" in entity.license
    assert len(entity.description) > 20
    assert "name" in entity.provenance


def test_tourism_adapter_records():
    """Validates official Department of Tourism data has verified status and opening hours."""
    adapter = TourismAdapter()
    records = adapter.fetch_raw_records("pondicherry", limit=2)
    assert len(records) > 0
    
    entity = adapter.transform_to_entity(records[0], city_id="pondicherry")
    assert entity.verification_status == VerificationStatusEnum.VERIFIED
    assert entity.opening_hours_verified is True
    assert entity.estimated_cost_inr >= 0
    assert "official_tourism" in entity.primary_source_id


def test_entity_normalizer():
    """Validates canonical name stripping, diacritics removal, and category mapping."""
    norm = EntityNormalizer()
    
    # Honorifics & accents stripping
    assert norm.canonical_name("Sri Kapaleeshwarar Temple") == "kapaleeshwarar temple"
    assert norm.canonical_name("Arulmigu Manakula Vinayagar Temple") == "manakula vinayagar temple"
    assert norm.canonical_name("The Promenade Beach") == "promenade beach"
    assert norm.canonical_name("Kāpālīśvarar") == "kapalisvarar"

    # Category normalization
    assert norm.normalize_category("Temple complex") == "spiritual"
    assert norm.normalize_category("botanical garden") == "nature"
    assert norm.normalize_category("Sandy Beach") == "beach"
    assert norm.normalize_category("Historic Museum") == "heritage"


def test_deduplicator_category_thresholds():
    """Validates category-dependent proximity thresholds: 35m for temples vs 500m for beaches."""
    repo = KnowledgeRepository()
    dedup = EntityDeduplicator(repo)

    # 1. Two separate temples 45 meters apart: MUST NOT MERGE
    temple_a = KnowledgeEntity(
        id="temple-shiva",
        city_id="chennai",
        name="Lord Shiva Shrine",
        category="spiritual",
        coordinates={"lat": 13.03360, "lng": 80.26970},
        primary_source_url="https://source-a.com/shiva"
    )
    repo.upsert_entity(temple_a)

    temple_b = KnowledgeEntity(
        id="temple-navagraha",
        city_id="chennai",
        name="Navagraha Shrine",
        category="spiritual",
        coordinates={"lat": 13.03400, "lng": 80.26970},  # ~44.5 meters north
        primary_source_url="https://source-b.com/navagraha"
    )
    res_entity, action = dedup.resolve_or_merge(temple_b)
    assert action == "inserted"  # Kept separate!

    # 2. Duplicate beach entry 120 meters apart: MUST MERGE (beach threshold is 500m)
    beach_a = KnowledgeEntity(
        id="beach-promenade",
        city_id="pondicherry",
        name="Promenade Beach",
        category="beach",
        coordinates={"lat": 11.93380, "lng": 79.83580},
    )
    repo.upsert_entity(beach_a)

    beach_b = KnowledgeEntity(
        id="beach-rock",
        city_id="pondicherry",
        name="Promenade Beach (Rock Beach)",
        category="beach",
        coordinates={"lat": 11.93480, "lng": 79.83580},  # ~111 meters north
    )
    res_beach, action_beach = dedup.resolve_or_merge(beach_b)
    assert action_beach == "merged"


def test_deduplicator_ambiguous_routing():
    """Validates that ambiguous matches are routed to review_required."""
    repo = KnowledgeRepository()
    dedup = EntityDeduplicator(repo)

    ent_1 = KnowledgeEntity(
        id="monument-french-war",
        city_id="pondicherry",
        name="French War Memorial",
        category="heritage",
        coordinates={"lat": 11.93320, "lng": 79.83540},
    )
    repo.upsert_entity(ent_1)

    # Very similar name, but distance is 180 meters (between 100m threshold and 2.5x threshold)
    ent_ambiguous = KnowledgeEntity(
        id="monument-memorial-hall",
        city_id="pondicherry",
        name="French War Memorial Hall",
        category="heritage",
        coordinates={"lat": 11.93480, "lng": 79.83540},  # ~178 meters
    )
    res, action = dedup.resolve_or_merge(ent_ambiguous)
    assert res.verification_status == VerificationStatusEnum.REVIEW_REQUIRED


def test_validator_missing_data_fallbacks():
    """Validates missing-data fallbacks: zero invented coords, unknown prices, category duration."""
    validator = EntityValidator()
    
    incomplete_entity = KnowledgeEntity(
        id="ent-incomplete",
        name="Mystery Point",
        category="nature",
        coordinates=None,  # Missing
        estimated_cost_inr=0,  # Missing
        duration_minutes=0,  # Missing
        opening_hours=None,  # Missing
    )
    
    validated, issues = validator.validate(incomplete_entity)
    
    assert "missing_coordinates" in issues
    assert validated.coordinates is None  # Never invented
    assert validated.price_status == PriceStatusEnum.UNKNOWN  # Not claimed exact
    assert validated.duration_minutes == 90  # Nature category conservative estimate
    assert validated.duration_estimated is True
    assert validated.opening_hours_verified is False


def test_ingestion_manager_lifecycle():
    """Validates end-to-end ingestion job execution with IngestionManager."""
    repo = KnowledgeRepository()
    manager = IngestionManager(repository=repo)
    
    job = manager.trigger_job(source_id="wikidata", city_id="pondicherry")
    assert job.status == "pending"
    
    summary = manager.execute_job(
        job_id=job.id,
        worker_id="test-worker-01",
        city_id="pondicherry",
        limit=3
    )
    assert summary["success"] is True
    assert summary["processed"] == 3
    
    completed_job = repo.get_job(job.id)
    assert completed_job.status == "completed"
    assert completed_job.processed_records == 3
    
    entities = repo.find_entities(city_id="pondicherry")
    assert len(entities) >= 3
