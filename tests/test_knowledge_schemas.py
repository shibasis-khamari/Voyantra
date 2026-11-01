"""
Tests for Phase 1: Unified Knowledge Schemas & Storage
Validates schema defaults, field-level provenance, non-destructive read adapters, and atomic job leasing.
"""
import pytest
from datetime import datetime, timezone, timedelta
from backend.app.schemas.knowledge import (
    KnowledgeEntity,
    KnowledgeDocument,
    KnowledgeChunk,
    IngestionJob,
    KnowledgeSource,
    FieldProvenance,
    VerificationStatusEnum,
    SourceTypeEnum,
    PriceStatusEnum,
)
from backend.app.schemas.place import Place, CategoryEnum, BudgetTierEnum, Coordinates
from backend.app.schemas.hotel import Hotel
from backend.app.services.knowledge.storage.knowledge_repository import KnowledgeRepository


def test_knowledge_entity_schema_defaults():
    """Validates that verification_status defaults to unverified and price_status to unknown."""
    entity = KnowledgeEntity(
        id="ent-test-01",
        name="Test Heritage Monument"
    )
    assert entity.verification_status == VerificationStatusEnum.UNVERIFIED
    assert entity.price_status == PriceStatusEnum.UNKNOWN
    assert entity.estimated_cost_inr == 0
    assert entity.opening_hours_verified is False
    assert entity.entity_type == "place"
    assert entity.provenance == {}


def test_field_provenance_tracking():
    """Validates provenance tracking on individual fields."""
    prov = FieldProvenance(
        source_id="wikidata",
        source_url="https://www.wikidata.org/wiki/Q12345",
        license="CC0 1.0",
        confidence=0.95
    )
    entity = KnowledgeEntity(
        id="ent-test-02",
        name="Auroville Matrimandir",
        provenance={"name": prov, "coordinates": prov}
    )
    assert "name" in entity.provenance
    assert entity.provenance["name"].source_id == "wikidata"
    assert entity.provenance["name"].license == "CC0 1.0"
    assert entity.provenance["name"].confidence == 0.95


def test_read_adapter_from_place():
    """Validates non-destructive conversion from Place catalog item to KnowledgeEntity."""
    repo = KnowledgeRepository()
    test_place = Place(
        id="pondicherry-promenade-beach",
        city_id="pondicherry",
        name="Promenade Beach",
        category=CategoryEnum.BEACH,
        sub_category="Ocean Promenade",
        description="Famous rocky seaside promenade with colonial heritage.",
        highlights=["French War Memorial", "Gandhi Statue", "Sunset views"],
        budget_tier=BudgetTierEnum.BUDGET,
        estimated_cost_inr=0,
        duration_minutes=90,
        coordinates=Coordinates(lat=11.9338, lng=79.8358),
        address="Goubert Avenue, White Town, Puducherry",
        image_url="https://images.unsplash.com/photo-promenade",
        verification_status="verified",
        source_url="https://pondytourism.py.gov.in/promenade"
    )
    entity = repo.entity_from_place(test_place)
    
    assert entity.id == "pondicherry-promenade-beach"
    assert entity.city_id == "pondicherry"
    assert entity.entity_type == "place"
    assert entity.category == "beach"
    assert entity.coordinates["lat"] == 11.9338
    assert entity.coordinates["lng"] == 79.8358
    assert entity.verification_status == VerificationStatusEnum.VERIFIED
    assert "name" in entity.provenance
    assert entity.provenance["name"].source_id == "voyantra_catalog"


def test_read_adapter_unverified_by_default():
    """Validates that a place without explicit verified status converts to unverified."""
    repo = KnowledgeRepository()
    raw_place = {
        "id": "new-unverified-spot",
        "city_id": "chennai",
        "name": "Secret Beach Cave",
        "category": "nature",
        "description": "Newly submitted beach cave.",
        "coordinates": {"lat": 13.08, "lng": 80.27},
        "budget_tier": "budget",
        "estimated_cost_inr": 0,
        "duration_minutes": 60,
        "address": "ECR, Chennai",
        "image_url": "https://example.com/cave.jpg"
    }
    entity = repo.entity_from_place(raw_place)
    assert entity.verification_status == VerificationStatusEnum.UNVERIFIED
    assert entity.price_status == PriceStatusEnum.UNKNOWN


def test_read_adapter_from_hotel():
    """Validates non-destructive conversion from Hotel catalog item to KnowledgeEntity."""
    repo = KnowledgeRepository()
    test_hotel = Hotel(
        id="htl-villa-shanti",
        city_id="pondicherry",
        name="Villa Shanti",
        description="19th-century French colonial heritage townhouse hotel.",
        budget_tier=BudgetTierEnum.LUXURY,
        price_per_night_inr=7500,
        coordinates=Coordinates(lat=11.9320, lng=79.8340),
        address="Rue Suffren, White Town",
        image_url="https://images.unsplash.com/villa-shanti",
        amenities=["Courtyard Restaurant", "Free WiFi", "Heritage Architecture"],
        proximity_tag="White Town / Promenade"
    )
    entity = repo.entity_from_hotel(test_hotel)
    assert entity.id == "htl-villa-shanti"
    assert entity.entity_type == "hotel"
    assert entity.category == "hotel"
    assert entity.estimated_cost_inr == 7500
    assert entity.price_status == PriceStatusEnum.ESTIMATED
    assert "Courtyard Restaurant" in entity.amenities


def test_read_adapter_from_restaurant():
    """Validates non-destructive conversion of cafe/dining Place to restaurant entity."""
    repo = KnowledgeRepository()
    cafe = Place(
        id="pondy-cafe-des-arts",
        city_id="pondicherry",
        name="Café des Arts",
        category=CategoryEnum.CAFE,
        description="Bohemian French cafe serving baguettes and coffee.",
        budget_tier=BudgetTierEnum.MODERATE,
        estimated_cost_inr=450,
        duration_minutes=60,
        coordinates=Coordinates(lat=11.9315, lng=79.8335),
        address="Rue Suffren, White Town",
        image_url="https://images.unsplash.com/cafe-des-arts",
    )
    entity = repo.entity_from_restaurant(cafe)
    assert entity.entity_type == "restaurant"
    assert entity.category == "cafe"
    assert entity.estimated_cost_inr == 450


def test_knowledge_repository_crud():
    """Tests CRUD operations and entity counting in the knowledge repository."""
    repo = KnowledgeRepository()
    ent = KnowledgeEntity(
        id="ent-crud-01",
        city_id="pondicherry",
        name="Auroville Visitor Centre",
        category="spiritual"
    )
    repo.upsert_entity(ent)
    
    fetched = repo.get_entity("ent-crud-01")
    assert fetched is not None
    assert fetched.name == "Auroville Visitor Centre"
    
    found = repo.find_entities(city_id="pondicherry", category="spiritual")
    assert len(found) >= 1
    assert any(e.id == "ent-crud-01" for e in found)


def test_knowledge_document_and_chunks():
    """Tests document upsertion, chunking, and deactivation lifecycle."""
    repo = KnowledgeRepository()
    doc = KnowledgeDocument(
        id="doc-guide-01",
        source_id="voyantra_website",
        url="https://voyantra.com/guides/pondicherry",
        title="Complete Guide to White Town Pondicherry",
        raw_content="White town features French colonial villas and rocky promenades.",
        cleaned_content="White town features French colonial villas and rocky promenades.",
        content_hash="abc123hash"
    )
    repo.upsert_document(doc)
    
    chunks = [
        KnowledgeChunk(
            id="chk-01",
            document_id=doc.id,
            chunk_index=0,
            content="White town features French colonial villas.",
            content_hash="hash01",
            city_id="pondicherry"
        ),
        KnowledgeChunk(
            id="chk-02",
            document_id=doc.id,
            chunk_index=1,
            content="The rocky promenade offers beautiful sunrise views.",
            content_hash="hash02",
            city_id="pondicherry"
        ),
    ]
    count = repo.upsert_chunks(chunks)
    assert count == 2
    
    found = repo.find_chunks(document_id=doc.id)
    assert len(found) == 2
    
    deactivated = repo.deactivate_document_chunks(doc.id)
    assert deactivated == 2
    active_found = repo.find_chunks(document_id=doc.id, is_active=True)
    assert len(active_found) == 0


def test_atomic_job_leasing():
    """Tests worker ownership, atomic job claiming, and lease safety."""
    repo = KnowledgeRepository()
    job = IngestionJob(
        id="job-sync-01",
        source_id="wikidata",
        job_type="dataset_sync",
        status="pending"
    )
    repo.create_job(job)
    
    # Worker 1 claims job
    claimed_1 = repo.claim_job(worker_id="worker-node-1", lease_seconds=120)
    assert claimed_1 is not None
    assert claimed_1.id == "job-sync-01"
    assert claimed_1.status == "running"
    assert claimed_1.worker_id == "worker-node-1"
    assert claimed_1.lease_expires_at is not None
    
    # Worker 2 attempts to claim while lease is active -> None
    claimed_2 = repo.claim_job(worker_id="worker-node-2", lease_seconds=120)
    assert claimed_2 is None
    
    # Worker 1 reports progress
    progress_ok = repo.update_job_progress(
        job_id="job-sync-01",
        worker_id="worker-node-1",
        processed_records=25,
        offset=25
    )
    assert progress_ok is True
    
    # Worker 1 completes job
    completed = repo.complete_job(job_id="job-sync-01", worker_id="worker-node-1")
    assert completed is True
    
    updated_job = repo.get_job("job-sync-01")
    assert updated_job.status == "completed"
    assert updated_job.processed_records == 25


def test_job_bounded_retries():
    """Tests bounded retries when a job fails repeatedly."""
    repo = KnowledgeRepository()
    job = IngestionJob(
        id="job-failing-01",
        source_id="osm",
        job_type="dataset_sync",
        status="pending",
        max_retries=2
    )
    repo.create_job(job)
    
    claimed = repo.claim_job(worker_id="worker-node-1", lease_seconds=60)
    assert claimed is not None
    
    # First failure -> goes to pending for retry
    repo.fail_job(job_id="job-failing-01", worker_id="worker-node-1", error_message="Network timeout", max_retries=2)
    j1 = repo.get_job("job-failing-01")
    assert j1.status == "pending"
    assert j1.retry_count == 1
    
    # Second claim & failure -> goes to permanently_failed
    claimed_again = repo.claim_job(worker_id="worker-node-2", lease_seconds=60)
    assert claimed_again is not None
    repo.fail_job(job_id="job-failing-01", worker_id="worker-node-2", error_message="DNS failure", max_retries=2)
    j2 = repo.get_job("job-failing-01")
    assert j2.status == "permanently_failed"
    assert j2.retry_count == 2
    assert len(j2.error_logs) == 2
