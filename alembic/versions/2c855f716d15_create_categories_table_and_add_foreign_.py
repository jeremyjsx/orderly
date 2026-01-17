"""create_categories_table_and_add_foreign_key_to_products

Revision ID: 2c855f716d15
Revises: a1b2c3d4e5f6
Create Date: 2026-01-16 22:31:28.726319

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2c855f716d15"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "categories",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_categories_name"), "categories", ["name"], unique=True)
    op.create_index(op.f("ix_categories_slug"), "categories", ["slug"], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("fk_products_category_id", "products", type_="foreignkey")
    op.drop_index(op.f("ix_products_category_id"), table_name="products")
    op.drop_index(op.f("ix_categories_slug"), table_name="categories")
    op.drop_index(op.f("ix_categories_name"), table_name="categories")
    op.drop_table("categories")
