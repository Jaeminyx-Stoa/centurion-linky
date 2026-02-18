import uuid

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    clinic_name: str = Field(..., min_length=1, max_length=200)
    clinic_slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9_-]+$")
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=1, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    role: str
    clinic_id: uuid.UUID | None = None

    model_config = {"from_attributes": True}
