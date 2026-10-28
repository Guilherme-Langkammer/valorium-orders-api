from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserRegister(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        email = value.strip().lower()

        if (
            email.count("@") != 1
            or not email.split("@")[0]
            or "." not in email.split("@")[1]
            or email.startswith("@")
            or email.endswith(".")
        ):
            raise ValueError("Invalid email address")

        return email


class UserLogin(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: str
    is_active: bool
    created_at: datetime


class TokenRead(BaseModel):
    access_token: str
    token_type: str = "bearer"