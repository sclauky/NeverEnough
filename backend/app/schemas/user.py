
from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    model_validator,
)


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


class UserPasswordUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(
        min_length=1,
        max_length=128,
        repr=False,
    )

    new_password: str = Field(
        min_length=12,
        max_length=128,
        repr=False,
    )

    confirm_new_password: str = Field(
        min_length=12,
        max_length=128,
        repr=False,
    )

    @model_validator(mode="after")
    def validate_new_passwords(self):
        if self.new_password != self.confirm_new_password:
            raise ValueError("New passwords do not match.")

        if self.new_password == self.current_password:
            raise ValueError("New password must be different.")

        return self
