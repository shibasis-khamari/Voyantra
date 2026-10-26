from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any
from ...schemas.auth import (
    UserLoginRequest,
    UserRegisterRequest,
    AuthTokenResponse,
    UserProfile,
    UserRoleEnum,
    UsersListResponse,
    UserRoleUpdateRequest,
    UserActionResponse
)
from ...services.auth_service import auth_service
from ...core.dependencies import require_admin

router = APIRouter(prefix="/auth", tags=["Authentication & User Management"])

@router.post("/login", response_model=AuthTokenResponse)
def login(req: UserLoginRequest):
    """
    Authenticates User (Traveler) or Admin.
    Pre-configured Demo Accounts:
    - User Demo: user@voyantra.com / user123
    - Admin Demo: admin@voyantra.com / admin123
    """
    res = auth_service.authenticate_user(req)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email credentials or role mismatch. Please check your password."
        )
    return res

@router.post("/register", response_model=AuthTokenResponse)
def register(req: UserRegisterRequest):
    """
    Registers a new Traveler User or Admin account in MongoDB.
    """
    res = auth_service.register_user(req)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )
    return res

@router.get("/demo-accounts")
def get_demo_accounts():
    """Returns pre-configured demo account hints for quick UI testing."""
    return {
        "user_demo": {
            "email": "user@voyantra.com",
            "password": "user123",
            "role": "user",
            "description": "Standard Traveler account"
        },
        "admin_demo": {
            "email": "admin@voyantra.com",
            "password": "admin123",
            "role": "admin",
            "description": "Administrator account with management rights"
        }
    }

@router.get("/users", response_model=UsersListResponse)
def get_all_users(current_admin: Dict[str, Any] = Depends(require_admin)):
    """
    Administrator endpoint: Retrieves all registered users in MongoDB.
    Requires valid admin Bearer token.
    """
    users = auth_service.list_users()
    return UsersListResponse(users=users, total=len(users))

@router.delete("/users/{user_id}", response_model=UserActionResponse)
def delete_user(user_id: str, current_admin: Dict[str, Any] = Depends(require_admin)):
    """
    Administrator endpoint: Deletes a user account from MongoDB.
    Guarded against self-deletion and seed-admin deletion.
    """
    success, message = auth_service.delete_user(user_id, current_admin)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    return UserActionResponse(success=True, message=message)

@router.patch("/users/{user_id}/role", response_model=UserActionResponse)
def update_user_role(
    user_id: str,
    req: UserRoleUpdateRequest,
    current_admin: Dict[str, Any] = Depends(require_admin)
):
    """
    Administrator endpoint: Promotes or demotes user role between Traveler and Admin.
    """
    profile, message = auth_service.update_user_role(user_id, req.role, current_admin)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    return UserActionResponse(success=True, message=message, user=profile)
