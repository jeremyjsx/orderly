import uuid

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=3, max_length=255)
    price: float = Field(gt=0)
    stock: int = Field(gt=0)
    category_id: uuid.UUID


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = Field(default=None, min_length=3)
    price: float | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)
    category_id: uuid.UUID | None = None
    is_active: bool | None = None


class ProductPublic(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    price: float
    stock: int
    category_id: uuid.UUID
    image_url: str | None
    is_active: bool
