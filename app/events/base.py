import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator


class Event(BaseModel):
    """Base class for all domain events in the system."""

    event_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        description="Unique identifier for this event instance",
    )
    event_type: str = Field(
        description="Type of event (e.g., 'order.created', 'payment.processed')"
    )
    event_version: int = Field(
        default=1,
        ge=1,
        description="Version of the event schema for backward compatibility",
    )
    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the event occurred",
    )
    producer: str = Field(description="Service or component that produced this event")

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        """Validate event type format."""
        if not v or not v.strip():
            raise ValueError("event_type cannot be empty")
        if "." not in v:
            raise ValueError(
                "event_type should follow pattern 'domain.action' "
                "(e.g., 'order.created')"
            )
        return v.strip()

    @field_validator("producer")
    @classmethod
    def validate_producer(cls, v: str) -> str:
        """Validate producer name."""
        if not v or not v.strip():
            raise ValueError("producer cannot be empty")
        return v.strip()

    class Config:
        json_encoders = {
            uuid.UUID: str,
            datetime: lambda v: v.isoformat(),
        }
