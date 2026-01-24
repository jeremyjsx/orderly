import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator

from app.modules.orders.models import OrderStatus
from app.modules.products.schemas import ProductPublic


class OrderCreate(BaseModel):
    pass


class OrderItemPublic(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    quantity: int
    price: float
    subtotal: float
    product: ProductPublic | None = None


class OrderPublic(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    status: OrderStatus
    total: float
    items: list[OrderItemPublic]
    created_at: datetime
    updated_at: datetime
    driver_id: uuid.UUID | None = None


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class LocationUpdate(BaseModel):
    latitude: float
    longitude: float
    timestamp: datetime | None = None

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        if not -90.0 <= v <= 90.0:
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        if not -180.0 <= v <= 180.0:
            raise ValueError("Longitude must be between -180 and 180")
        return v
