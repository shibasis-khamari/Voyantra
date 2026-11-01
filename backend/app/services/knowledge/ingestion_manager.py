"""
Voyantra Knowledge Ingestion Manager
Coordinates multi-source data ingestion with persistent worker leasing,
batch checkpointing, deduplication, and dead-letter error handling.
"""
import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from ...schemas.knowledge import IngestionJob, KnowledgeEntity, utc_now_iso
from .storage.knowledge_repository import knowledge_repository, KnowledgeRepository
from .ingestion.wikidata_adapter import WikidataAdapter
from .ingestion.osm_adapter import OSMAdapter
from .ingestion.wikipedia_adapter import WikipediaAdapter
from .ingestion.tourism_adapter import TourismAdapter
from .processing.normalizer import EntityNormalizer
from .processing.deduplicator import EntityDeduplicator
from .processing.validator import EntityValidator

logger = logging.getLogger("voyantra.knowledge.ingestion")


class IngestionManager:
    def __init__(self, repository: Optional[KnowledgeRepository] = None):
        self.repo = repository or knowledge_repository
        self.normalizer = EntityNormalizer()
        self.deduplicator = EntityDeduplicator(self.repo)
        self.validator = EntityValidator()
        self.adapters = {
            "wikidata": WikidataAdapter(),
            "osm": OSMAdapter(),
            "wikipedia": WikipediaAdapter(),
            "official_tourism": TourismAdapter(),
        }

    def trigger_job(self, source_id: str, city_id: str = "pondicherry", job_type: str = "dataset_sync") -> IngestionJob:
        """Creates a pending ingestion job in the repository."""
        job_id = f"job-{source_id}-{city_id}-{uuid.uuid4().hex[:6]}"
        job = IngestionJob(
            id=job_id,
            source_id=source_id,
            job_type=job_type,
            status="pending",
            retry_count=0,
            max_retries=3,
            total_records=0,
            processed_records=0,
            offset=0,
        )
        return self.repo.create_job(job)

    def execute_job(
        self,
        job_id: str,
        worker_id: str,
        city_id: str = "pondicherry",
        limit: int = 50,
        lease_seconds: int = 120
    ) -> Dict[str, Any]:
        """Claims and runs an ingestion job idempotently with lease renewal and batch checkpointing."""
        job = self.repo.get_job(job_id)
        if not job:
            return {"success": False, "error": f"Job {job_id} not found"}

        # Claim the job if it's pending or expired
        claimed = self.repo.claim_job(worker_id=worker_id, lease_seconds=lease_seconds)
        if not claimed or claimed.id != job_id:
            # If claimed is not this job, verify if this job is already claimed by us
            if job.worker_id != worker_id or job.status != "running":
                return {"success": False, "error": f"Unable to claim lease for job {job_id}"}

        adapter = self.adapters.get(job.source_id)
        if not adapter:
            self.repo.fail_job(job_id, worker_id, f"No adapter registered for source '{job.source_id}'")
            return {"success": False, "error": f"Unrecognized source: {job.source_id}"}

        try:
            raw_records = adapter.fetch_raw_records(city_id=city_id, limit=limit)
            job.total_records = len(raw_records)
            self.repo.update_job_progress(job_id, worker_id, processed_records=0, offset=0)

            processed_count = 0
            inserted_count = 0
            merged_count = 0

            for idx, raw_record in enumerate(raw_records):
                try:
                    # 1. Transform raw record
                    entity = adapter.transform_to_entity(raw_record, city_id=city_id)
                    
                    # 2. Normalize entity fields
                    normalized_entity = self.normalizer.normalize(entity)

                    # 3. Validate entity fields (missing coordinates, unverified price)
                    valid_entity, validation_issues = self.validator.validate(normalized_entity)

                    # 4. Multi-signal deduplication
                    resolved_entity, action = self.deduplicator.resolve_or_merge(valid_entity)

                    # 5. Persist
                    self.repo.upsert_entity(resolved_entity)

                    if action == "inserted":
                        inserted_count += 1
                    else:
                        merged_count += 1

                    processed_count += 1

                    # Checkpoint every 5 records or at end
                    if processed_count % 5 == 0 or processed_count == len(raw_records):
                        self.repo.update_job_progress(
                            job_id=job_id,
                            worker_id=worker_id,
                            processed_records=processed_count,
                            offset=processed_count
                        )
                        self.repo.renew_job_lease(job_id, worker_id, lease_seconds=lease_seconds)

                except Exception as rec_err:
                    err_payload = {
                        "record_index": idx,
                        "error": str(rec_err),
                        "timestamp": utc_now_iso(),
                    }
                    self.repo.update_job_progress(
                        job_id=job_id,
                        worker_id=worker_id,
                        processed_records=processed_count,
                        offset=processed_count,
                        error_log=err_payload
                    )

            self.repo.complete_job(job_id, worker_id)
            return {
                "success": True,
                "job_id": job_id,
                "total": len(raw_records),
                "processed": processed_count,
                "inserted": inserted_count,
                "merged": merged_count,
            }

        except Exception as job_err:
            self.repo.fail_job(job_id, worker_id, str(job_err))
            return {"success": False, "error": str(job_err)}


ingestion_manager = IngestionManager()
