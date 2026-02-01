import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"email": "user@example.com", "password": "SecurePass123!"}
        }
    )


class UserUpdate(BaseModel):
    email: EmailStr | None = None

    model_config = ConfigDict(
        json_schema_extra={"example": {"email": "newemail@example.com"}}
    )


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "current_password": "OldPass123!",
                "new_password": "NewSecurePass456!",
            }
        }
    )


class UserPublic(BaseModel):
    id: uuid.UUID
    email: EmailStr
    role: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "role": "USER",
            }
        }
    )
