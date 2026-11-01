from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class VerificationStatusEnum(str, Enum):
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    ESTIMATED = "estimated"
    REVIEW_REQUIRED = "review_required"


class SourceTypeEnum(str, Enum):
    WIKIDATA = "wikidata"
    OSM = "osm"
    WIKIPEDIA = "wikipedia"
    OFFICIAL_TOURISM = "official_tourism"
    WEBSITE_CRAWL = "website_crawl"
    LEGACY_CATALOG = "legacy_catalog"
    MANUAL = "manual"


class PriceStatusEnum(str, Enum):
    EXACT = "exact"
    ESTIMATED = "estimated"
    UNKNOWN = "unknown"


class FieldProvenance(BaseModel):
    source_id: str
    source_url: Optional[str] = None
    license: Optional[str] = None
    retrieved_at: str = Field(default_factory=utc_now_iso)
    confidence: float = 1.0


class KnowledgeSource(BaseModel):
    id: str
    name: str
    source_type: SourceTypeEnum
    base_url: Optional[str] = None
    license_name: str
    license_url: Optional[str] = None
    attribution_required: bool = True
    rate_limit_per_minute: int = 30
    is_active: bool = True


class KnowledgeEntity(BaseModel):
    id: str
    entity_type: str = "place"  # "place", "hotel", "restaurant", "policy", "attraction"
    city_id: Optional[str] = None  # "pondicherry", "chennai", or None
    name: str
    alternate_names: List[str] = Field(default_factory=list)
    description: str = ""
    category: Optional[str] = None
    sub_category: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None  # {"lat": float, "lng": float}
    address: Optional[str] = None
    budget_tier: Optional[str] = None  # "budget", "moderate", "luxury"
    estimated_cost_inr: Optional[int] = 0
    price_status: PriceStatusEnum = PriceStatusEnum.UNKNOWN
    duration_minutes: Optional[int] = None
    duration_estimated: bool = False
    opening_hours: Optional[str] = None
    opening_hours_verified: bool = False
    weekly_closing_days: List[str] = Field(default_factory=list)
    highlights: List[str] = Field(default_factory=list)
    amenities: List[str] = Field(default_factory=list)
    dietary_options: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    image_url: Optional[str] = None
    rating: Optional[float] = 4.5
    review_count: Optional[int] = 100
    
    # Verification and Provenance tracking
    verification_status: VerificationStatusEnum = VerificationStatusEnum.UNVERIFIED
    provenance: Dict[str, FieldProvenance] = Field(default_factory=dict)
    primary_source_id: Optional[str] = None
    primary_source_url: Optional[str] = None
    license: Optional[str] = None
    attribution: Optional[str] = None
    content_hash: Optional[str] = None
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class KnowledgeDocument(BaseModel):
    id: str
    source_id: str
    url: str
    title: str
    raw_content: str = ""
    cleaned_content: str = ""
    content_hash: str = ""
    version: int = 1
    is_active: bool = True
    license: Optional[str] = None
    fetched_at: str = Field(default_factory=utc_now_iso)
    language: str = "en"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeChunk(BaseModel):
    id: str
    document_id: Optional[str] = None
    entity_id: Optional[str] = None
    chunk_index: int = 0
    content: str
    content_hash: str = ""
    token_count: int = 0
    heading_context: Optional[str] = None
    language: str = "en"
    is_active: bool = True
    vector_id: Optional[str] = None
    source_url: Optional[str] = None
    source_title: Optional[str] = None
    city_id: Optional[str] = None
    category: Optional[str] = None
    created_at: str = Field(default_factory=utc_now_iso)


class IngestionJob(BaseModel):
    id: str
    source_id: str
    job_type: str = "dataset_sync"  # "dataset_sync", "website_crawl", "reindex"
    status: str = "pending"  # "pending", "running", "completed", "failed", "permanently_failed"
    worker_id: Optional[str] = None
    lease_expires_at: Optional[str] = None
    heartbeat_at: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    total_records: int = 0
    processed_records: int = 0
    offset: int = 0
    error_logs: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)
