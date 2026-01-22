"""add_driver_role

Revision ID: fa2dde6b65ef
Revises: l3m4n5o6p7q8
Create Date: 2026-01-21 19:19:14.617701

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fa2dde6b65ef"
down_revision: str | Sequence[str] | None = "l3m4n5o6p7q8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add driver role and driver_id to orders table."""
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS check_role")
    op.execute(
        "ALTER TABLE users ADD CONSTRAINT check_role CHECK (role IN ('admin', 'user', 'driver'))"
    )

    op.add_column("orders", sa.Column("driver_id", sa.UUID(), nullable=True))

    op.create_foreign_key(
        "fk_orders_driver_id", "orders", "users", ["driver_id"], ["id"]
    )

    op.create_index(op.f("ix_orders_driver_id"), "orders", ["driver_id"], unique=False)


def downgrade() -> None:
    """Remove driver role and driver_id column."""
    op.drop_index(op.f("ix_orders_driver_id"), table_name="orders")

    op.drop_constraint("fk_orders_driver_id", "orders", type_="foreignkey")

    op.drop_column("orders", "driver_id")

    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS check_role")
    op.execute(
        "ALTER TABLE users ADD CONSTRAINT check_role CHECK (role IN ('admin', 'user'))"
    )
