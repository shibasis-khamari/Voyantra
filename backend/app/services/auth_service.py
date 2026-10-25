import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
import jwt

from ..schemas.auth import UserLoginRequest, UserRegisterRequest, UserProfile, AuthTokenResponse, UserRoleEnum
from ..core.database import db_manager, hash_password, verify_password
from ..core.config import settings

class AuthService:
    def create_access_token(self, user_id: str, email: str, role: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
        payload = {
            "sub": user_id,
            "email": email,
            "role": role,
            "exp": expire,
            "iat": datetime.now(timezone.utc)
        }
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    def decode_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            return payload
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None

    def authenticate_user(self, req: UserLoginRequest) -> Optional[AuthTokenResponse]:
        user_doc = db_manager.find_user_by_email(req.email)
        if not user_doc:
            return None
        
        # Verify password with bcrypt
        stored_pw = user_doc.get("password", "")
        if not verify_password(req.password, stored_pw):
            return None
        
        # Check role match if strictly enforced or default to stored role
        user_role = user_doc.get("role", UserRoleEnum.USER.value)
        if req.role and req.role.value != user_role:
            pass

        user_id = str(user_doc.get("id", user_doc.get("_id", uuid.uuid4().hex[:8])))
        email = user_doc.get("email")

        profile = UserProfile(
            id=user_id,
            name=user_doc.get("name", "Traveler"),
            email=email,
            role=UserRoleEnum(user_role),
            avatar_url=user_doc.get("avatar_url", None)
        )

        token = self.create_access_token(user_id=user_id, email=email, role=user_role)
        return AuthTokenResponse(
            access_token=token,
            token_type="bearer",
            user=profile
        )

    def register_user(self, req: UserRegisterRequest) -> Optional[AuthTokenResponse]:
        existing = db_manager.find_user_by_email(req.email)
        if existing:
            return None
        
        user_id = f"usr-{uuid.uuid4().hex[:8]}"
        hashed = hash_password(req.password)
        new_user = {
            "id": user_id,
            "name": req.name,
            "email": req.email.lower(),
            "password": hashed,
            "role": req.role.value
        }
        
        saved = db_manager.insert_user(new_user)
        profile = UserProfile(
            id=saved["id"],
            name=saved["name"],
            email=saved["email"],
            role=UserRoleEnum(saved["role"])
        )

        token = self.create_access_token(user_id=saved["id"], email=saved["email"], role=saved["role"])
        return AuthTokenResponse(
            access_token=token,
            token_type="bearer",
            user=profile
        )

auth_service = AuthService()
