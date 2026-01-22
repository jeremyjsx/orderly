from typing import TYPE_CHECKING
import uuid
from datetime import datetime
from enum import Enum as EnumType

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.modules.orders.models import Order


class Role(EnumType):
    ADMIN = "admin"
    USER = "user"
    DRIVER = "driver"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=True
    )
    role: Mapped[Role] = mapped_column(
        String(10), nullable=False, default=Role.USER.value
    )
    orders: Mapped[list["Order"]] = relationship("Order", foreign_keys="Order.driver_id", back_populates="driver")
