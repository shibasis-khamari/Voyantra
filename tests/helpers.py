"""Shared test helpers."""
from backend.app.services.auth_service import auth_service
from backend.app.schemas.auth import UserLoginRequest


def auth_headers(email: str = "user@voyantra.com", password: str = "user123") -> dict:
    """Bearer headers for a seeded demo account (in-memory fallback users)."""
    res = auth_service.authenticate_user(UserLoginRequest(email=email, password=password))
    assert res is not None, f"Could not authenticate {email}"
    return {"Authorization": f"Bearer {res.access_token}"}
