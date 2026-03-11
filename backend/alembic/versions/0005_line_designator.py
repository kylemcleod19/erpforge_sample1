"""add line_designator to product_bom_items

Revision ID: 0005
Revises: 0004
Create Date: 2026-03-11

"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "product_bom_items",
        sa.Column("line_designator", sa.String(100), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("product_bom_items", "line_designator")
