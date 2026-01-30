import uuid

from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    slug: str = Field(min_length=2, max_length=255)
    is_active: bool = Field(default=True)


class CategoryPublic(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    slug: str
    is_active: bool
    image_url: str | None


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    slug: str | None = Field(default=None, min_length=2, max_length=255)
    is_active: bool | None = None
