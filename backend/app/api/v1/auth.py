from fastapi import APIRouter, HTTPException, status
from ...schemas.auth import UserLoginRequest, UserRegisterRequest, AuthTokenResponse, UserProfile, UserRoleEnum
from ...services.auth_service import auth_service

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
