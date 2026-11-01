"""
Tests for Phase 12: Admin Security & SSRF Hardening
Validates JWT admin role authorization and SSRF prevention on administrative endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.auth_service import auth_service
from backend.app.schemas.auth import UserLoginRequest

client = TestClient(app)


@pytest.fixture
def admin_token():
    """Generates valid JWT bearer token for System Administrator."""
    res = auth_service.authenticate_user(UserLoginRequest(
        email="admin@voyantra.com",
        password="admin123"
    ))
    assert res is not None, "Failed to authenticate demo admin account"
    return res.access_token


@pytest.fixture
def user_token():
    """Generates valid JWT bearer token for standard Traveler User."""
    res = auth_service.authenticate_user(UserLoginRequest(
        email="user@voyantra.com",
        password="user123"
    ))
    assert res is not None, "Failed to authenticate demo traveler user account"
    return res.access_token


def test_public_knowledge_endpoints():
    """Health and stats endpoints should be accessible without credentials."""
    resp = client.get("/api/v1/knowledge/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "VTKE" in data["engine"]

    sources_resp = client.get("/api/v1/knowledge/sources")
    assert sources_resp.status_code == 200
    assert len(sources_resp.json()) > 0


def test_anonymous_caller_blocked_from_admin_endpoints():
    """Calls without token must be rejected with 401 Unauthorized."""
    # Ingestion trigger
    ingest_resp = client.post("/api/v1/knowledge/ingestion/run", json={"source_id": "wikidata"})
    assert ingest_resp.status_code == 401

    # Website crawl
    crawl_resp = client.post("/api/v1/knowledge/website/crawl", json={"url": "https://voyantra.com"})
    assert crawl_resp.status_code == 401


def test_standard_user_blocked_with_403_forbidden(user_token):
    """Standard user tokens must receive 403 Forbidden on admin-only routes."""
    headers = {"Authorization": f"Bearer {user_token}"}
    
    ingest_resp = client.post(
        "/api/v1/knowledge/ingestion/run",
        json={"source_id": "wikidata"},
        headers=headers
    )
    assert ingest_resp.status_code == 403
    assert "Administrator privilege required" in ingest_resp.json()["detail"]

    crawl_resp = client.post(
        "/api/v1/knowledge/website/crawl",
        json={"url": "https://voyantra.com"},
        headers=headers
    )
    assert crawl_resp.status_code == 403


def test_admin_allowed_to_trigger_ingestion(admin_token):
    """Admin token should be authorized to trigger ingestion."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = client.post(
        "/api/v1/knowledge/ingestion/run",
        json={"source_id": "tourism", "city_id": "pondicherry", "limit": 2},
        headers=headers
    )
    # If source is tourism (official_tourism), test should validate source check or execute
    assert resp.status_code in [200, 400]
    if resp.status_code == 400:
        assert "Valid sources" in resp.json()["detail"]


def test_ssrf_attacks_rejected(admin_token):
    """Admin token attempting SSRF attack against loopback, cloud metadata, or unallowed domain is rejected with 400."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # 1. AWS/GCP cloud metadata IP
    meta_resp = client.post(
        "/api/v1/knowledge/website/crawl",
        json={"url": "http://169.254.169.254/latest/meta-data/"},
        headers=headers
    )
    assert meta_resp.status_code == 400
    assert "SSRF policy violation" in meta_resp.json()["detail"]

    # 2. Arbitrary unapproved external domain
    evil_resp = client.post(
        "/api/v1/knowledge/website/crawl",
        json={"url": "https://malicious-attacker.com/leak"},
        headers=headers
    )
    assert evil_resp.status_code == 400
    assert "not in allowed crawl domains" in evil_resp.json()["detail"]
