import uuid

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=3, max_length=255)
    price: float = Field(gt=0)
    stock: int = Field(gt=0)
    category_id: uuid.UUID
    image_url: str = Field(min_length=3, max_length=255)


class ProductPublic(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    price: float
    stock: int
    category_id: uuid.UUID
    image_url: str
    is_active: bool
