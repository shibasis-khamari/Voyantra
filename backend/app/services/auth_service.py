import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Tuple
import jwt

from ..schemas.auth import (
    UserLoginRequest,
    UserRegisterRequest,
    UserProfile,
    AuthTokenResponse,
    UserRoleEnum,
    UserManagementProfile
)
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
            "role": req.role.value,
            "created_at": datetime.now(timezone.utc).isoformat()
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

    def list_users(self) -> List[UserManagementProfile]:
        """Lists all registered users for admin review (passwords excluded)."""
        raw_users = db_manager.list_all_users()
        profiles = []
        for u in raw_users:
            role_val = u.get("role", "user")
            try:
                role_enum = UserRoleEnum(role_val)
            except ValueError:
                role_enum = UserRoleEnum.USER
            profiles.append(
                UserManagementProfile(
                    id=str(u.get("id")),
                    name=u.get("name", "Traveler"),
                    email=u.get("email", ""),
                    role=role_enum,
                    avatar_url=u.get("avatar_url"),
                    created_at=u.get("created_at")
                )
            )
        return profiles

    def delete_user(self, user_id: str, current_user: Dict[str, Any]) -> Tuple[bool, str]:
        """Deletes a user account with safety checks preventing self-deletion and seed-admin deletion."""
        target = db_manager.find_user_by_id(user_id)
        if not target:
            return False, "User not found."

        target_email = target.get("email", "").lower()
        if target_email == "admin@voyantra.com":
            return False, "The default System Administrator account cannot be deleted."

        current_email = current_user.get("email", "").lower()
        if target_email == current_email:
            return False, "You cannot delete your own active administrator account."

        success = db_manager.delete_user(user_id)
        if success:
            return True, f"User {target.get('name', target_email)} has been successfully removed."
        return False, "Failed to remove user from database."

    def update_user_role(self, user_id: str, new_role: UserRoleEnum, current_user: Dict[str, Any]) -> Tuple[Optional[UserManagementProfile], str]:
        """Updates user's role (admin / traveler) with security guards."""
        target = db_manager.find_user_by_id(user_id)
        if not target:
            return None, "User not found."

        target_email = target.get("email", "").lower()
        if target_email == "admin@voyantra.com" and new_role != UserRoleEnum.ADMIN:
            return None, "The default System Administrator account role cannot be downgraded."

        current_email = current_user.get("email", "").lower()
        if target_email == current_email and new_role != UserRoleEnum.ADMIN:
            return None, "You cannot remove admin privileges from your own active session."

        updated = db_manager.update_user_role(user_id, new_role.value)
        if not updated:
            return None, "Failed to update user role."

        return UserManagementProfile(
            id=str(updated.get("id")),
            name=updated.get("name", "Traveler"),
            email=updated.get("email", ""),
            role=UserRoleEnum(updated.get("role", new_role.value)),
            avatar_url=updated.get("avatar_url"),
            created_at=updated.get("created_at")
        ), f"Role for {updated.get('name', target_email)} successfully updated to {new_role.value}."

auth_service = AuthService()
