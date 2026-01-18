import uuid
from typing import Literal

from pydantic import BaseModel

from app.events.base import Event


class PaymentProcessedPayload(BaseModel):
    order_id: uuid.UUID
    user_id: uuid.UUID
    amount: float
    payment_method: str
    transaction_id: str
    status: str


class PaymentProcessedEvent(Event):
    event_type: Literal["payment.processed"] = "payment.processed"
    payload: PaymentProcessedPayload
