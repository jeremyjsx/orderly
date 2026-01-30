"""Add image_url to categories and make products.image_url nullable

Revision ID: s3a4b5c6d7e8
Revises: r2s3t4u5v6w7
Create Date: 2026-01-29 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "s3a4b5c6d7e8"
down_revision: str | None = "r2s3t4u5v6w7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "categories",
        sa.Column("image_url", sa.Text(), nullable=True),
    )
    op.alter_column(
        "products",
        "image_url",
        existing_type=sa.Text(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "products",
        "image_url",
        existing_type=sa.Text(),
        nullable=False,
    )
    op.drop_column("categories", "image_url")
