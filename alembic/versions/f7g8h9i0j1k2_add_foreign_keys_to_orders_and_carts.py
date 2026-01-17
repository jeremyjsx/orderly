"""add_foreign_keys_to_orders_and_carts

Revision ID: f7g8h9i0j1k2
Revises: a1b2c3d4e5f6
Create Date: 2026-01-16 21:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f7g8h9i0j1k2"
down_revision: str | Sequence[str] | None = "2c855f716d15"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add Foreign Key constraint to carts.user_id.

    Note: orders.user_id does NOT have FK constraint to allow user deletion
    while preserving orders with their original user_id (business requirement).
    """
    # Add FK constraint to carts.user_id with ON DELETE CASCADE
    # This matches current app behavior (carts are deleted when user is deleted)
    op.create_foreign_key(
        "fk_carts_user_id",
        "carts",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Remove Foreign Key constraint."""
    op.drop_constraint("fk_carts_user_id", "carts", type_="foreignkey")
