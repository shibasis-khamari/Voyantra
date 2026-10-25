from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum

class UserRoleEnum(str, Enum):
    USER = "user"
    ADMIN = "admin"

class UserLoginRequest(BaseModel):
    email: str
    password: str
    role: UserRoleEnum = UserRoleEnum.USER

class UserRegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: UserRoleEnum = UserRoleEnum.USER

class UserProfile(BaseModel):
    id: str
    name: str
    email: str
    role: UserRoleEnum
    avatar_url: Optional[str] = None

class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile
