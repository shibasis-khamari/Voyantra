"""
Voyantra Knowledge Repository
Provides unified persistence for knowledge entities, documents, chunks, and ingestion jobs
with seamless MongoDB Atlas backing and resilient in-memory fallback for offline/test environments.
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union
import uuid
from pymongo import ReturnDocument

from ....core.database import db_manager
from ....schemas.knowledge import (
    KnowledgeEntity,
    KnowledgeDocument,
    KnowledgeChunk,
    IngestionJob,
    KnowledgeSource,
    FieldProvenance,
    VerificationStatusEnum,
    SourceTypeEnum,
    PriceStatusEnum,
    utc_now_iso,
)
from ....schemas.place import Place, CategoryEnum, BudgetTierEnum
from ....schemas.hotel import Hotel


class KnowledgeRepository:
    def __init__(self, in_memory_only: bool = False):
        self.in_memory_only = in_memory_only
        # In-memory storage stores dictionaries keyed by ID
        self._memory_entities: Dict[str, Dict[str, Any]] = {}
        self._memory_documents: Dict[str, Dict[str, Any]] = {}
        self._memory_chunks: Dict[str, Dict[str, Any]] = {}
        self._memory_jobs: Dict[str, Dict[str, Any]] = {}
        self._memory_sources: Dict[str, Dict[str, Any]] = {}
        self._seed_default_sources()

    def _seed_default_sources(self):
        defaults = [
            KnowledgeSource(
                id="wikidata",
                name="Wikidata Knowledge Graph",
                source_type=SourceTypeEnum.WIKIDATA,
                base_url="https://www.wikidata.org",
                license_name="CC0 1.0 Universal",
                license_url="https://creativecommons.org/publicdomain/zero/1.0/",
                attribution_required=False,
                rate_limit_per_minute=60,
            ),
            KnowledgeSource(
                id="osm",
                name="OpenStreetMap Overpass",
                source_type=SourceTypeEnum.OSM,
                base_url="https://overpass-api.de",
                license_name="Open Database License (ODbL) 1.0",
                license_url="https://opendatacommons.org/licenses/odbl/",
                attribution_required=True,
                rate_limit_per_minute=30,
            ),
            KnowledgeSource(
                id="wikipedia",
                name="Wikipedia MediaWiki API",
                source_type=SourceTypeEnum.WIKIPEDIA,
                base_url="https://en.wikipedia.org",
                license_name="CC BY-SA 4.0",
                license_url="https://creativecommons.org/licenses/by-sa/4.0/",
                attribution_required=True,
                rate_limit_per_minute=60,
            ),
            KnowledgeSource(
                id="official_tourism",
                name="Official Department of Tourism (Puducherry & Tamil Nadu)",
                source_type=SourceTypeEnum.OFFICIAL_TOURISM,
                base_url="https://pondytourism.py.gov.in",
                license_name="Official Public Sector Information",
                license_url="https://pondytourism.py.gov.in",
                attribution_required=True,
                rate_limit_per_minute=20,
            ),
            KnowledgeSource(
                id="voyantra_website",
                name="Voyantra Official Travel Platform",
                source_type=SourceTypeEnum.WEBSITE_CRAWL,
                base_url="https://voyantra.com",
                license_name="Voyantra Proprietary Public Travel Information",
                attribution_required=True,
                rate_limit_per_minute=120,
            ),
            KnowledgeSource(
                id="voyantra_catalog",
                name="Voyantra Verified Catalog",
                source_type=SourceTypeEnum.LEGACY_CATALOG,
                license_name="Voyantra Open Tourism Dataset",
                attribution_required=True,
                rate_limit_per_minute=1000,
            ),
        ]
        for src in defaults:
            self._memory_sources[src.id] = src.model_dump()

    # -------------------------------------------------------------
    # MongoDB Collection Accessors
    # -------------------------------------------------------------
    def _get_collection(self, name: str):
        if self.in_memory_only:
            return None
        if db_manager.is_connected and db_manager.db is not None:
            return db_manager.get_collection(name)
        return None

    # -------------------------------------------------------------
    # Knowledge Sources
    # -------------------------------------------------------------
    def get_source(self, source_id: str) -> Optional[KnowledgeSource]:
        col = self._get_collection("knowledge_sources")
        if col is not None:
            doc = col.find_one({"id": source_id})
            if doc:
                doc.pop("_id", None)
                return KnowledgeSource(**doc)
        data = self._memory_sources.get(source_id)
        return KnowledgeSource(**data) if data else None

    def upsert_source(self, source: KnowledgeSource) -> KnowledgeSource:
        s_dict = source.model_dump()
        col = self._get_collection("knowledge_sources")
        if col is not None:
            col.update_one({"id": source.id}, {"$set": s_dict}, upsert=True)
        self._memory_sources[source.id] = s_dict
        return source

    def list_sources(self) -> List[KnowledgeSource]:
        col = self._get_collection("knowledge_sources")
        if col is not None:
            docs = list(col.find({"is_active": True}))
            for d in docs:
                d.pop("_id", None)
            if docs:
                return [KnowledgeSource(**d) for d in docs]
        return [KnowledgeSource(**d) for d in self._memory_sources.values() if d.get("is_active", True)]

    # -------------------------------------------------------------
    # Knowledge Entities
    # -------------------------------------------------------------
    def upsert_entity(self, entity: KnowledgeEntity) -> KnowledgeEntity:
        entity.updated_at = utc_now_iso()
        e_dict = entity.model_dump()
        col = self._get_collection("knowledge_entities")
        if col is not None:
            col.update_one({"id": entity.id}, {"$set": e_dict}, upsert=True)
        self._memory_entities[entity.id] = e_dict
        return entity

    def get_entity(self, entity_id: str) -> Optional[KnowledgeEntity]:
        col = self._get_collection("knowledge_entities")
        if col is not None:
            doc = col.find_one({"id": entity_id})
            if doc:
                doc.pop("_id", None)
                return KnowledgeEntity(**doc)
        data = self._memory_entities.get(entity_id)
        return KnowledgeEntity(**data) if data else None

    def find_entities(
        self,
        city_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        category: Optional[str] = None,
        verification_status: Optional[str] = None,
        limit: int = 50,
        skip: int = 0
    ) -> List[KnowledgeEntity]:
        col = self._get_collection("knowledge_entities")
        if col is not None:
            q: Dict[str, Any] = {}
            if city_id:
                q["city_id"] = city_id
            if entity_type:
                q["entity_type"] = entity_type
            if category:
                q["category"] = category
            if verification_status:
                q["verification_status"] = verification_status
            docs = list(col.find(q).skip(skip).limit(limit))
            for d in docs:
                d.pop("_id", None)
            return [KnowledgeEntity(**d) for d in docs]

        results = []
        for d in self._memory_entities.values():
            if city_id and d.get("city_id") != city_id:
                continue
            if entity_type and d.get("entity_type") != entity_type:
                continue
            if category and d.get("category") != category:
                continue
            if verification_status and d.get("verification_status") != verification_status:
                continue
            results.append(KnowledgeEntity(**d))
        return results[skip : skip + limit]

    def count_entities(self, query: Optional[Dict[str, Any]] = None) -> int:
        col = self._get_collection("knowledge_entities")
        if col is not None:
            return col.count_documents(query or {})
        return len(self._memory_entities)

    # -------------------------------------------------------------
    # Knowledge Documents
    # -------------------------------------------------------------
    def upsert_document(self, document: KnowledgeDocument) -> KnowledgeDocument:
        d_dict = document.model_dump()
        col = self._get_collection("knowledge_documents")
        if col is not None:
            col.update_one({"id": document.id}, {"$set": d_dict}, upsert=True)
        self._memory_documents[document.id] = d_dict
        return document

    def get_document(self, doc_id: str) -> Optional[KnowledgeDocument]:
        col = self._get_collection("knowledge_documents")
        if col is not None:
            doc = col.find_one({"id": doc_id})
            if doc:
                doc.pop("_id", None)
                return KnowledgeDocument(**doc)
        data = self._memory_documents.get(doc_id)
        return KnowledgeDocument(**data) if data else None

    def get_document_by_url(self, url: str) -> Optional[KnowledgeDocument]:
        col = self._get_collection("knowledge_documents")
        if col is not None:
            doc = col.find_one({"url": url})
            if doc:
                doc.pop("_id", None)
                return KnowledgeDocument(**doc)
        for d in self._memory_documents.values():
            if d.get("url") == url:
                return KnowledgeDocument(**d)
        return None

    # -------------------------------------------------------------
    # Knowledge Chunks
    # -------------------------------------------------------------
    def upsert_chunks(self, chunks: List[KnowledgeChunk]) -> int:
        if not chunks:
            return 0
        col = self._get_collection("knowledge_chunks")
        if col is not None:
            for chk in chunks:
                col.update_one({"id": chk.id}, {"$set": chk.model_dump()}, upsert=True)
        for chk in chunks:
            self._memory_chunks[chk.id] = chk.model_dump()
        return len(chunks)

    def get_chunk(self, chunk_id: str) -> Optional[KnowledgeChunk]:
        col = self._get_collection("knowledge_chunks")
        if col is not None:
            doc = col.find_one({"id": chunk_id})
            if doc:
                doc.pop("_id", None)
                return KnowledgeChunk(**doc)
        data = self._memory_chunks.get(chunk_id)
        return KnowledgeChunk(**data) if data else None

    def find_chunks(
        self,
        document_id: Optional[str] = None,
        entity_id: Optional[str] = None,
        city_id: Optional[str] = None,
        is_active: bool = True,
        limit: int = 50
    ) -> List[KnowledgeChunk]:
        col = self._get_collection("knowledge_chunks")
        if col is not None:
            q: Dict[str, Any] = {"is_active": is_active}
            if document_id:
                q["document_id"] = document_id
            if entity_id:
                q["entity_id"] = entity_id
            if city_id:
                q["city_id"] = city_id
            docs = list(col.find(q).limit(limit))
            for d in docs:
                d.pop("_id", None)
            return [KnowledgeChunk(**d) for d in docs]

        results = []
        for d in self._memory_chunks.values():
            if d.get("is_active") != is_active:
                continue
            if document_id and d.get("document_id") != document_id:
                continue
            if entity_id and d.get("entity_id") != entity_id:
                continue
            if city_id and d.get("city_id") != city_id:
                continue
            results.append(KnowledgeChunk(**d))
        return results[:limit]

    def deactivate_document_chunks(self, document_id: str) -> int:
        col = self._get_collection("knowledge_chunks")
        if col is not None:
            res = col.update_many({"document_id": document_id}, {"$set": {"is_active": False}})
            count = res.modified_count
        else:
            count = 0
            for d in self._memory_chunks.values():
                if d.get("document_id") == document_id and d.get("is_active", True):
                    d["is_active"] = False
                    count += 1
        return count

    # -------------------------------------------------------------
    # Ingestion Jobs with Atomic Leases & Worker Ownership
    # -------------------------------------------------------------
    def create_job(self, job: IngestionJob) -> IngestionJob:
        j_dict = job.model_dump()
        col = self._get_collection("knowledge_ingestion_jobs")
        if col is not None:
            col.update_one({"id": job.id}, {"$set": j_dict}, upsert=True)
        self._memory_jobs[job.id] = j_dict
        return job

    def claim_job(self, worker_id: str, lease_seconds: int = 120) -> Optional[IngestionJob]:
        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()
        lease_expires = (now_dt + timedelta(seconds=lease_seconds)).isoformat()

        col = self._get_collection("knowledge_ingestion_jobs")
        if col is not None:
            doc = col.find_one_and_update(
                {
                    "$or": [
                        {"status": "pending"},
                        {"status": "running", "lease_expires_at": {"$lt": now_iso}}
                    ]
                },
                {
                    "$set": {
                        "status": "running",
                        "worker_id": worker_id,
                        "lease_expires_at": lease_expires,
                        "heartbeat_at": now_iso,
                        "updated_at": now_iso,
                    }
                },
                return_document=ReturnDocument.AFTER
            )
            if doc:
                doc.pop("_id", None)
                return IngestionJob(**doc)
            return None

        for j_id, j in self._memory_jobs.items():
            st = j.get("status")
            exp = j.get("lease_expires_at")
            if st == "pending" or (st == "running" and exp and exp < now_iso):
                j["status"] = "running"
                j["worker_id"] = worker_id
                j["lease_expires_at"] = lease_expires
                j["heartbeat_at"] = now_iso
                j["updated_at"] = now_iso
                return IngestionJob(**j)
        return None

    def renew_job_lease(self, job_id: str, worker_id: str, lease_seconds: int = 120) -> bool:
        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()
        lease_expires = (now_dt + timedelta(seconds=lease_seconds)).isoformat()

        col = self._get_collection("knowledge_ingestion_jobs")
        if col is not None:
            res = col.update_one(
                {"id": job_id, "worker_id": worker_id, "status": "running"},
                {
                    "$set": {
                        "lease_expires_at": lease_expires,
                        "heartbeat_at": now_iso,
                        "updated_at": now_iso,
                    }
                }
            )
            return res.modified_count > 0

        j = self._memory_jobs.get(job_id)
        if j and j.get("worker_id") == worker_id and j.get("status") == "running":
            j["lease_expires_at"] = lease_expires
            j["heartbeat_at"] = now_iso
            j["updated_at"] = now_iso
            return True
        return False

    def update_job_progress(
        self,
        job_id: str,
        worker_id: str,
        processed_records: int,
        offset: int,
        error_log: Optional[Dict[str, Any]] = None
    ) -> bool:
        now_iso = utc_now_iso()
        update_doc: Dict[str, Any] = {
            "$set": {
                "processed_records": processed_records,
                "offset": offset,
                "heartbeat_at": now_iso,
                "updated_at": now_iso,
            }
        }
        if error_log:
            update_doc["$push"] = {"error_logs": error_log}

        col = self._get_collection("knowledge_ingestion_jobs")
        if col is not None:
            res = col.update_one({"id": job_id, "worker_id": worker_id}, update_doc)
            return res.modified_count > 0

        j = self._memory_jobs.get(job_id)
        if j and j.get("worker_id") == worker_id:
            j["processed_records"] = processed_records
            j["offset"] = offset
            j["heartbeat_at"] = now_iso
            j["updated_at"] = now_iso
            if error_log:
                j.setdefault("error_logs", []).append(error_log)
            return True
        return False

    def complete_job(self, job_id: str, worker_id: str) -> bool:
        now_iso = utc_now_iso()
        col = self._get_collection("knowledge_ingestion_jobs")
        if col is not None:
            res = col.update_one(
                {"id": job_id, "worker_id": worker_id},
                {"$set": {"status": "completed", "lease_expires_at": None, "updated_at": now_iso}}
            )
            return res.modified_count > 0

        j = self._memory_jobs.get(job_id)
        if j and j.get("worker_id") == worker_id:
            j["status"] = "completed"
            j["lease_expires_at"] = None
            j["updated_at"] = now_iso
            return True
        return False

    def fail_job(self, job_id: str, worker_id: str, error_message: str, max_retries: int = 3) -> bool:
        now_iso = utc_now_iso()
        col = self._get_collection("knowledge_ingestion_jobs")
        if col is not None:
            job_doc = col.find_one({"id": job_id})
            retries = (job_doc.get("retry_count", 0) + 1) if job_doc else 1
            new_status = "permanently_failed" if retries >= max_retries else "pending"
            col.update_one(
                {"id": job_id},
                {
                    "$set": {
                        "status": new_status,
                        "retry_count": retries,
                        "worker_id": None,
                        "lease_expires_at": None,
                        "updated_at": now_iso,
                    },
                    "$push": {
                        "error_logs": {
                            "timestamp": now_iso,
                            "error": error_message,
                            "retry_attempt": retries,
                        }
                    }
                }
            )
            return True

        j = self._memory_jobs.get(job_id)
        if j:
            retries = j.get("retry_count", 0) + 1
            j["retry_count"] = retries
            j["status"] = "permanently_failed" if retries >= max_retries else "pending"
            j["worker_id"] = None
            j["lease_expires_at"] = None
            j["updated_at"] = now_iso
            j.setdefault("error_logs", []).append({
                "timestamp": now_iso,
                "error": error_message,
                "retry_attempt": retries,
            })
            return True
        return False

    def get_job(self, job_id: str) -> Optional[IngestionJob]:
        col = self._get_collection("knowledge_ingestion_jobs")
        if col is not None:
            doc = col.find_one({"id": job_id})
            if doc:
                doc.pop("_id", None)
                return IngestionJob(**doc)
        data = self._memory_jobs.get(job_id)
        return IngestionJob(**data) if data else None

    # -------------------------------------------------------------
    # Non-Destructive Read Adapters for Existing Catalog
    # -------------------------------------------------------------
    def entity_from_place(self, place: Union[Place, Dict[str, Any]]) -> KnowledgeEntity:
        """Adapts an existing Place catalog item to a standardized KnowledgeEntity."""
        p_dict = place.model_dump() if isinstance(place, Place) else dict(place)
        
        # Coordinates normalization
        coords = p_dict.get("coordinates")
        if hasattr(coords, "model_dump"):
            coords = coords.model_dump()
        elif isinstance(coords, dict):
            coords = {"lat": float(coords.get("lat", 0.0)), "lng": float(coords.get("lng", 0.0))}
        else:
            coords = None

        # Category and Budget Tier
        cat = p_dict.get("category")
        cat_val = cat.value if hasattr(cat, "value") else str(cat) if cat else None
        b_tier = p_dict.get("budget_tier")
        b_val = b_tier.value if hasattr(b_tier, "value") else str(b_tier) if b_tier else None

        # Verification Status defaults to UNVERIFIED unless explicitly verified
        v_status_raw = p_dict.get("verification_status", "unverified")
        try:
            v_status = VerificationStatusEnum(v_status_raw)
        except Exception:
            v_status = VerificationStatusEnum.UNVERIFIED

        # Price status: Exact only if verified with non-zero cost; else unknown/estimated
        cost = p_dict.get("estimated_cost_inr", 0) or 0
        if cost > 0:
            p_status = PriceStatusEnum.ESTIMATED
        else:
            p_status = PriceStatusEnum.UNKNOWN

        # Build provenance
        src_url = p_dict.get("source_url")
        retrieved_at = p_dict.get("source_verified_at") or p_dict.get("last_updated_at") or utc_now_iso()
        prov = {
            "name": FieldProvenance(
                source_id="voyantra_catalog",
                source_url=src_url,
                license="Voyantra Open Tourism Dataset",
                retrieved_at=retrieved_at,
                confidence=1.0 if v_status == VerificationStatusEnum.VERIFIED else 0.85
            ),
            "coordinates": FieldProvenance(
                source_id="voyantra_catalog",
                source_url=src_url,
                license="Voyantra Open Tourism Dataset",
                retrieved_at=retrieved_at,
                confidence=1.0 if coords else 0.0
            )
        }

        dietary = p_dict.get("dietary_options") or []
        diet_str = [d.value if hasattr(d, "value") else str(d) for d in dietary]

        return KnowledgeEntity(
            id=p_dict.get("id", f"ent-{uuid.uuid4().hex[:8]}"),
            entity_type="place",
            city_id=p_dict.get("city_id"),
            name=p_dict.get("name", "Unknown Place"),
            alternate_names=[],
            description=p_dict.get("description", ""),
            category=cat_val,
            sub_category=p_dict.get("sub_category"),
            coordinates=coords,
            address=p_dict.get("address"),
            budget_tier=b_val,
            estimated_cost_inr=cost,
            price_status=p_status,
            duration_minutes=p_dict.get("duration_minutes", 60),
            duration_estimated=False,
            opening_hours=p_dict.get("opening_hours"),
            opening_hours_verified=p_dict.get("opening_hours_verified", False),
            weekly_closing_days=p_dict.get("weekly_closing_days") or [],
            highlights=p_dict.get("highlights") or [],
            amenities=[],
            dietary_options=diet_str,
            tags=p_dict.get("tags") or [],
            image_url=p_dict.get("image_url"),
            rating=p_dict.get("rating", 4.5),
            review_count=p_dict.get("review_count", 100),
            verification_status=v_status,
            provenance=prov,
            primary_source_id="voyantra_catalog",
            primary_source_url=src_url,
            license="Voyantra Open Tourism Dataset",
            attribution="Voyantra Catalog",
            created_at=p_dict.get("last_updated_at") or utc_now_iso(),
            updated_at=utc_now_iso(),
        )

    def entity_from_hotel(self, hotel: Union[Hotel, Dict[str, Any]]) -> KnowledgeEntity:
        """Adapts an existing Hotel catalog item to a standardized KnowledgeEntity."""
        h_dict = hotel.model_dump() if isinstance(hotel, Hotel) else dict(hotel)
        coords = h_dict.get("coordinates")
        if hasattr(coords, "model_dump"):
            coords = coords.model_dump()
        elif isinstance(coords, dict):
            coords = {"lat": float(coords.get("lat", 0.0)), "lng": float(coords.get("lng", 0.0))}
        else:
            coords = None

        b_tier = h_dict.get("budget_tier")
        b_val = b_tier.value if hasattr(b_tier, "value") else str(b_tier) if b_tier else None

        rate = h_dict.get("price_per_night_inr", 0) or 0
        prov = {
            "name": FieldProvenance(
                source_id="voyantra_catalog",
                source_url=h_dict.get("booking_url"),
                license="Voyantra Open Tourism Dataset",
                retrieved_at=utc_now_iso(),
                confidence=0.9
            )
        }

        dietary = h_dict.get("dietary_options") or []
        diet_str = [d.value if hasattr(d, "value") else str(d) for d in dietary]

        return KnowledgeEntity(
            id=h_dict.get("id", f"ent-htl-{uuid.uuid4().hex[:8]}"),
            entity_type="hotel",
            city_id=h_dict.get("city_id"),
            name=h_dict.get("name", "Unknown Hotel"),
            alternate_names=[],
            description=h_dict.get("description", ""),
            category="hotel",
            sub_category=h_dict.get("proximity_tag"),
            coordinates=coords,
            address=h_dict.get("address"),
            budget_tier=b_val,
            estimated_cost_inr=rate,
            price_status=PriceStatusEnum.ESTIMATED if rate > 0 else PriceStatusEnum.UNKNOWN,
            duration_minutes=None,
            duration_estimated=False,
            opening_hours=None,
            opening_hours_verified=False,
            weekly_closing_days=[],
            highlights=[],
            amenities=h_dict.get("amenities") or [],
            dietary_options=diet_str,
            tags=[h_dict.get("proximity_tag")] if h_dict.get("proximity_tag") else [],
            image_url=h_dict.get("image_url"),
            rating=h_dict.get("rating", 4.2),
            review_count=h_dict.get("review_count", 80),
            verification_status=VerificationStatusEnum.VERIFIED,
            provenance=prov,
            primary_source_id="voyantra_catalog",
            primary_source_url=h_dict.get("booking_url"),
            license="Voyantra Open Tourism Dataset",
            attribution="Voyantra Catalog",
            created_at=utc_now_iso(),
            updated_at=utc_now_iso(),
        )

    def entity_from_restaurant(self, place: Union[Place, Dict[str, Any]]) -> KnowledgeEntity:
        """Adapts an existing dining/cafe Place item to a standardized KnowledgeEntity."""
        ent = self.entity_from_place(place)
        ent.entity_type = "restaurant"
        return ent


knowledge_repository = KnowledgeRepository()
