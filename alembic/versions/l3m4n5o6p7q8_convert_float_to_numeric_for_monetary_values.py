"""convert_float_to_numeric_for_monetary_values

Revision ID: l3m4n5o6p7q8
Revises: f7g8h9i0j1k2
Create Date: 2026-01-16 22:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "l3m4n5o6p7q8"
down_revision: str | Sequence[str] | None = "f7g8h9i0j1k2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Convert Float columns to Numeric(10, 2) for monetary values."""
    # Convert products.price
    op.alter_column(
        "products",
        "price",
        type_=postgresql.NUMERIC(10, 2),
        existing_type=sa.Float(),
        postgresql_using="price::numeric(10, 2)",
    )

    # Convert orders.total
    op.alter_column(
        "orders",
        "total",
        type_=postgresql.NUMERIC(10, 2),
        existing_type=sa.Float(),
        postgresql_using="total::numeric(10, 2)",
    )

    # Convert order_items.price
    op.alter_column(
        "order_items",
        "price",
        type_=postgresql.NUMERIC(10, 2),
        existing_type=sa.Float(),
        postgresql_using="price::numeric(10, 2)",
    )

    # Convert order_items.subtotal
    op.alter_column(
        "order_items",
        "subtotal",
        type_=postgresql.NUMERIC(10, 2),
        existing_type=sa.Float(),
        postgresql_using="subtotal::numeric(10, 2)",
    )


def downgrade() -> None:
    """Convert Numeric columns back to Float."""
    # Convert products.price back to Float
    op.alter_column(
        "products",
        "price",
        type_=sa.Float(),
        existing_type=postgresql.NUMERIC(10, 2),
        postgresql_using="price::double precision",
    )

    # Convert orders.total back to Float
    op.alter_column(
        "orders",
        "total",
        type_=sa.Float(),
        existing_type=postgresql.NUMERIC(10, 2),
        postgresql_using="total::double precision",
    )

    # Convert order_items.price back to Float
    op.alter_column(
        "order_items",
        "price",
        type_=sa.Float(),
        existing_type=postgresql.NUMERIC(10, 2),
        postgresql_using="price::double precision",
    )

    # Convert order_items.subtotal back to Float
    op.alter_column(
        "order_items",
        "subtotal",
        type_=sa.Float(),
        existing_type=postgresql.NUMERIC(10, 2),
        postgresql_using="subtotal::double precision",
    )
