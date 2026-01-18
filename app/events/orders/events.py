import uuid
from typing import Literal

from pydantic import BaseModel

from app.events.base import Event
from app.modules.orders.schemas import OrderItemPublic


class OrderCreatedPayload(BaseModel):
    order_id: uuid.UUID
    user_id: uuid.UUID
    total: float
    items: list[OrderItemPublic]


class OrderCreatedEvent(Event):
    event_type: Literal["order.created"] = "order.created"
    payload: OrderCreatedPayload
