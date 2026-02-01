import uuid

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    slug: str = Field(min_length=2, max_length=255)
    is_active: bool = Field(default=True)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Electronics",
                "description": "Electronic devices and accessories",
                "slug": "electronics",
                "is_active": True,
            }
        }
    )


class CategoryPublic(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    slug: str
    is_active: bool
    image_url: str | None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Electronics",
                "description": "Electronic devices and accessories",
                "slug": "electronics",
                "is_active": True,
                "image_url": "https://s3.amazonaws.com/bucket/categories/electronics.jpg",
            }
        }
    )


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    slug: str | None = Field(default=None, min_length=2, max_length=255)
    is_active: bool | None = None

    model_config = ConfigDict(
        json_schema_extra={"example": {"description": "Updated description"}}
    )
