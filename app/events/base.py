import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class Event(BaseModel):
    event_id: uuid.UUID
    event_type: str
    event_version: int = Field(default=1)
    occurred_at: datetime
    producer: str
