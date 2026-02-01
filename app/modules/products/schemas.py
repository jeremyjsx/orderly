import uuid

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=3, max_length=255)
    price: float = Field(gt=0)
    stock: int = Field(gt=0)
    category_id: uuid.UUID

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Wireless Headphones",
                "description": "Bluetooth 5.0 headphones with noise cancellation",
                "price": 79.99,
                "stock": 150,
                "category_id": "550e8400-e29b-41d4-a716-446655440000",
            }
        }
    )


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=255)
    description: str | None = Field(default=None, min_length=3)
    price: float | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)
    category_id: uuid.UUID | None = None
    is_active: bool | None = None

    model_config = ConfigDict(
        json_schema_extra={"example": {"price": 69.99, "stock": 200}}
    )


class ProductPublic(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    price: float
    stock: int
    category_id: uuid.UUID
    image_url: str | None
    is_active: bool

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                "name": "Wireless Headphones",
                "description": "Bluetooth 5.0 headphones with noise cancellation",
                "price": 79.99,
                "stock": 150,
                "category_id": "550e8400-e29b-41d4-a716-446655440000",
                "image_url": "https://s3.amazonaws.com/bucket/products/headphones.jpg",
                "is_active": True,
            }
        }
    )
