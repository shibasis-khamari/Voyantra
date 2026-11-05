from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any

from .database import db_manager
from ..services.auth_service import auth_service
from ..schemas.auth import UserRoleEnum

security = HTTPBearer(auto_error=False)

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    """Validates signed Bearer JWT token and returns authenticated user."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required. Please sign in.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = credentials.credentials
    payload = auth_service.decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    email = payload.get("email")
    user = db_manager.find_user_by_email(email) if email else None
    if not user:
        # Role/identity always come from the database, never from token claims.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account no longer exists. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user


def get_user_id(user: Dict[str, Any]) -> str:
    """Stable string id for a user document (works for Mongo and in-memory users)."""
    return str(user.get("id") or user.get("_id"))


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """Returns the authenticated user, or None for anonymous / invalid tokens."""
    if not credentials or not credentials.credentials:
        return None
    payload = auth_service.decode_access_token(credentials.credentials)
    if not payload or not payload.get("email"):
        return None
    return db_manager.find_user_by_email(payload["email"])

def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Ensures caller holds administrator privilege."""
    role = current_user.get("role")
    if role != UserRoleEnum.ADMIN.value and role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privilege required to perform this action."
        )
    return current_user
