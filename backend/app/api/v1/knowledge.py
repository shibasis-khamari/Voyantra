"""
Voyantra Knowledge Engine Admin & Operational Endpoints
Provides administrative endpoints for dataset ingestion, website crawling,
indexing statistics, and hybrid search testing, with JWT admin authorization and SSRF protection.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, HttpUrl
from typing import Dict, Any, List, Optional

from ...core.config import settings
from ...core.dependencies import require_admin
from ...services.knowledge.storage.knowledge_repository import knowledge_repository
from ...services.knowledge.storage.vector_repository import vector_repository
from ...services.knowledge.ingestion_manager import ingestion_manager
from ...services.knowledge.ingestion.website_crawler import WebsiteCrawler, SSRFValidationError
from ...services.knowledge.retrieval.hybrid_retriever import hybrid_retriever
from ...schemas.knowledge import KnowledgeSource, IngestionJob, KnowledgeEntity

router = APIRouter(prefix="/knowledge", tags=["Unified Tourism Knowledge Engine (VTKE)"])


class IngestionRunRequest(BaseModel):
    source_id: str
    city_id: str = "pondicherry"
    limit: int = 50


class CrawlRequest(BaseModel):
    url: str


@router.get("/health")
def knowledge_health():
    """Health check endpoint for the knowledge engine."""
    return {
        "status": "healthy",
        "engine": "Voyantra Unified Tourism Knowledge Engine (VTKE)",
        "rag_enabled": getattr(settings, "KNOWLEDGE_RAG_ENABLED", True),
        "embedding_model": getattr(settings, "KNOWLEDGE_GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001"),
    }


@router.get("/stats")
def knowledge_stats():
    """Returns catalog, document, chunk, and vector index statistics."""
    v_stats = vector_repository.benchmark_index()
    entity_count = knowledge_repository.count_entities()
    sources = knowledge_repository.list_sources()

    return {
        "total_entities": entity_count,
        "active_sources": len(sources),
        "vector_index": v_stats,
    }


@router.get("/sources")
def list_knowledge_sources():
    """Lists registered knowledge sources with attribution and licensing."""
    return knowledge_repository.list_sources()


@router.post("/ingestion/run")
def trigger_ingestion(
    req: IngestionRunRequest,
    current_admin: Dict[str, Any] = Depends(require_admin)
):
    """
    Triggers dataset synchronization for a registered knowledge source.
    Requires administrator privilege.
    """
    valid_sources = ["wikidata", "osm", "wikipedia", "official_tourism"]
    if req.source_id not in valid_sources:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown source_id '{req.source_id}'. Valid sources: {valid_sources}"
        )

    job = ingestion_manager.trigger_job(source_id=req.source_id, city_id=req.city_id)
    worker_id = f"admin-{current_admin.get('id', 'adm')}"

    result = ingestion_manager.execute_job(
        job_id=job.id,
        worker_id=worker_id,
        city_id=req.city_id,
        limit=req.limit
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Ingestion execution failed")
        )

    return result


@router.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    """Retrieves progress and status of an ingestion job."""
    job = knowledge_repository.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingestion job '{job_id}' not found."
        )
    return job


@router.post("/website/crawl")
def crawl_website_page(
    req: CrawlRequest,
    current_admin: Dict[str, Any] = Depends(require_admin)
):
    """
    Safely crawls an approved Voyantra website URL with SSRF protection and content diffing.
    Requires administrator privilege.
    """
    crawler = WebsiteCrawler()
    try:
        res = crawler.crawl_page(req.url)
        if not res.get("success"):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Crawling failed with HTTP status {res.get('status_code')}"
            )
        # Avoid serializing full document model object in JSON response
        res.pop("document", None)
        return res
    except SSRFValidationError as ssrf_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"SSRF policy violation: {str(ssrf_err)}"
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Crawl operation encountered an unexpected error: {str(exc)}"
        )


@router.get("/search")
def test_hybrid_search(
    query: str = Query(..., min_length=2),
    city_id: Optional[str] = None,
    category: Optional[str] = None,
    top_k: int = Query(5, ge=1, le=20)
):
    """Test endpoint for hybrid lexical, vector, and structured retrieval."""
    results = hybrid_retriever.search(
        query=query,
        city_id=city_id,
        category=category,
        top_k=top_k
    )

    formatted = []
    for ent, score in results:
        formatted.append({
            "id": ent.id,
            "name": ent.name,
            "city_id": ent.city_id,
            "category": ent.category,
            "verification_status": ent.verification_status,
            "source": ent.attribution or ent.primary_source_id,
            "source_url": ent.primary_source_url,
            "score": round(score, 6),
        })

    return {
        "query": query,
        "city_id": city_id,
        "category": category,
        "results_count": len(formatted),
        "results": formatted
    }
