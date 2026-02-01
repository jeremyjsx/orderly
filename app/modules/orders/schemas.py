import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.modules.orders.models import OrderStatus
from app.modules.products.schemas import ProductPublic


class ShippingAddressCreate(BaseModel):
    recipient_name: str
    phone: str
    street: str
    city: str
    state: str
    postal_code: str
    country: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "recipient_name": "John Doe",
                "phone": "+1234567890",
                "street": "123 Main Street",
                "city": "New York",
                "state": "NY",
                "postal_code": "10001",
                "country": "USA",
            }
        }
    )


class ShippingAddressPublic(BaseModel):
    id: uuid.UUID
    recipient_name: str
    phone: str
    street: str
    city: str
    state: str
    postal_code: str
    country: str


class OrderCreate(BaseModel):
    shipping_address: ShippingAddressCreate


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
    shipping_address: ShippingAddressPublic | None = None
    created_at: datetime
    updated_at: datetime
    driver_id: uuid.UUID | None = None


class OrderStatusUpdate(BaseModel):
    status: OrderStatus

    model_config = ConfigDict(json_schema_extra={"example": {"status": "SHIPPED"}})


class LocationUpdate(BaseModel):
    latitude: float
    longitude: float
    timestamp: datetime | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "latitude": 40.7128,
                "longitude": -74.0060,
                "timestamp": "2026-01-30T12:00:00Z",
            }
        }
    )

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
