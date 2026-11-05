from pydantic import BaseModel, EmailStr
from typing import Optional, List
from enum import Enum

class UserRoleEnum(str, Enum):
    USER = "user"
    ADMIN = "admin"

class UserLoginRequest(BaseModel):
    email: str
    password: str
    role: UserRoleEnum = UserRoleEnum.USER

class UserRegisterRequest(BaseModel):
    # NOTE: no `role` field. Public registration always creates a traveler.
    # Extra fields sent by old clients (e.g. "role": "admin") are ignored.
    name: str
    email: str
    password: str

class UserProfile(BaseModel):
    id: str
    name: str
    email: str
    role: UserRoleEnum
    avatar_url: Optional[str] = None

class UserRoleUpdateRequest(BaseModel):
    role: UserRoleEnum

class UserManagementProfile(BaseModel):
    id: str
    name: str
    email: str
    role: UserRoleEnum
    avatar_url: Optional[str] = None
    created_at: Optional[str] = None

class UsersListResponse(BaseModel):
    users: List[UserManagementProfile]
    total: int

class UserActionResponse(BaseModel):
    success: bool
    message: str
    user: Optional[UserManagementProfile] = None

class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile
