import uuid
from datetime import datetime

from pydantic import BaseModel

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
