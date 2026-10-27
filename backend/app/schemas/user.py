from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    email: EmailStr

    username: str = Field(
        min_length=3,
        max_length=30,
        pattern=r"^[A-Za-z0-9_.-]+$",
    )

    password: str = Field(
        min_length=12,
        max_length=128,
        repr=False,
    )


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    profile_picture_url: str | None = None


class UserMe(UserPublic):
    email: EmailStr
    is_active: bool
    created_at: datetime
    
class UserLogin(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    email: EmailStr
    password: str = Field(
        min_length=1,
        max_length=128,
        repr=False,
    )


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    

class UserUpdate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=30,
        pattern=r"^[A-Za-z0-9_.-]+$",
    )


class UserEmailUpdate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    email: EmailStr
