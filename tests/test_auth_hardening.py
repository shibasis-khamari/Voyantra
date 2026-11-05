"""
Regression tests for the auth/authorization fixes:
  - public registration can never create an admin
  - tokens for unknown accounts are rejected (role claim is not trusted)
  - /chat/* requires authentication and is scoped to the signed-in user
  - conversations are not readable/deletable by other users
  - crowd reports are attributed to the logged-in user
"""
import datetime
import uuid

import jwt
import mongomock
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.core.database import db_manager
from helpers import auth_headers

client = TestClient(app)


def _register(role=None):
    body = {"name": "T", "email": f"{uuid.uuid4().hex[:8]}@example.com", "password": "pw-123456"}
    if role is not None:
        body["role"] = role
    r = client.post("/api/v1/auth/register", json=body)
    assert r.status_code == 200, r.text
    return r.json()


# ---------- registration / privilege escalation ----------

@pytest.mark.parametrize("role", [None, "user", "admin"])
def test_register_always_creates_traveler(role):
    data = _register(role)
    assert data["user"]["role"] == "user"
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    assert client.get("/api/v1/auth/users", headers=headers).status_code == 403


def test_token_for_unknown_account_is_rejected():
    forged = jwt.encode(
        {"sub": "x", "email": "ghost@example.com", "role": "admin",
         "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)},
        settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    r = client.get("/api/v1/auth/users", headers={"Authorization": f"Bearer {forged}"})
    assert r.status_code == 401


# ---------- chat requires auth ----------

@pytest.mark.parametrize("method,path,kwargs", [
    ("post", "/api/v1/chat/message", {"json": {"message": "hi"}}),
    ("get", "/api/v1/chat/conversations", {}),
    ("get", "/api/v1/chat/conversations/abc", {}),
    ("delete", "/api/v1/chat/conversations/abc", {}),
    ("get", "/api/v1/chat/memory", {}),
    ("put", "/api/v1/chat/memory", {"json": {}}),
    ("delete", "/api/v1/chat/memory", {}),
    ("post", "/api/v1/chat/transcribe", {}),
    ("post", "/api/v1/chat/synthesize", {"params": {"text": "hi"}}),
])
def test_chat_endpoints_require_token(method, path, kwargs):
    assert getattr(client, method)(path, **kwargs).status_code == 401


def test_user_id_query_param_cannot_impersonate():
    """?user_id=... must be ignored: memory belongs to the token's user only."""
    a, b = _register(), _register()
    ha = {"Authorization": f"Bearer {a['access_token']}"}
    hb = {"Authorization": f"Bearer {b['access_token']}"}
    client.put("/api/v1/chat/memory", json={"budget_tier": "luxury"}, headers=ha)
    seen_by_b = client.get(f"/api/v1/chat/memory?user_id={a['user']['id']}", headers=hb).json()
    assert seen_by_b.get("budget_tier") != "luxury"


# ---------- conversation isolation (needs a DB -> mongomock) ----------

@pytest.fixture
def fake_db(monkeypatch):
    mdb = mongomock.MongoClient()["voyantra_test"]
    monkeypatch.setattr(db_manager, "get_collection", lambda name: mdb[name])
    return mdb


def test_conversations_are_isolated_between_users(fake_db):
    a, b = _register(), _register()
    ha = {"Authorization": f"Bearer {a['access_token']}"}
    hb = {"Authorization": f"Bearer {b['access_token']}"}

    r = client.post("/api/v1/chat/message", json={"message": "Tell me about White Town Pondicherry"}, headers=ha)
    assert r.status_code == 200, r.text
    conv_id = r.json()["conversation_id"]

    assert client.get(f"/api/v1/chat/conversations/{conv_id}", headers=ha).status_code == 200
    # B cannot read, delete, list, or write into A's conversation
    assert client.get(f"/api/v1/chat/conversations/{conv_id}", headers=hb).status_code == 404
    assert client.delete(f"/api/v1/chat/conversations/{conv_id}", headers=hb).status_code == 404
    assert client.post("/api/v1/chat/message",
                       json={"message": "hello", "conversation_id": conv_id}, headers=hb).status_code == 404
    assert conv_id not in [c["id"] for c in client.get("/api/v1/chat/conversations", headers=hb).json()]
    # A still has it, and can delete it
    assert client.delete(f"/api/v1/chat/conversations/{conv_id}", headers=ha).status_code == 200


# ---------- crowd report attribution ----------

def test_crowd_report_uses_logged_in_user(monkeypatch):
    from backend.app.api.v1 import crowd
    captured = {}

    def fake_submit(request, client_ip, user_id):
        captured["user_id"] = user_id
        raise ValueError("stop here")  # -> 404, we only care about attribution

    monkeypatch.setattr(crowd.crowd_service, "submit_crowd_report", fake_submit)
    body = {"place_id": "x", "city_id": "pondicherry", "crowd_level": "moderate",
            "user_lat": 11.93, "user_lng": 79.83}
    client.post("/api/v1/crowd/report", json=body, headers=auth_headers())
    assert captured["user_id"] and captured["user_id"] != "None"
    client.post("/api/v1/crowd/report", json=body)
    assert captured["user_id"] is None
