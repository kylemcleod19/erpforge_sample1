"""bom line item enrichment and compliance tracking

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-09
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Phase 3: BOM line item enrichment
    op.add_column("product_bom_items", sa.Column("reference_designator", sa.String(50), nullable=True))
    op.add_column("product_bom_items", sa.Column("component_type", sa.String(30), nullable=True))
    op.add_column("product_bom_items", sa.Column("notes", sa.Text(), nullable=True))

    # Phase 3: alternate parts table
    op.create_table(
        "bom_item_alternates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bom_item_id", sa.Integer(), nullable=False),
        sa.Column("alternate_product_id", sa.Integer(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["bom_item_id"], ["product_bom_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["alternate_product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Phase 4: compliance tracking table
    op.create_table(
        "product_compliance",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("scope", sa.String(20), nullable=False),
        sa.Column("cert_type", sa.String(50), nullable=False),
        sa.Column("cert_number", sa.String(100), nullable=True),
        sa.Column("issued_date", sa.Date(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("document_url", sa.String(2048), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("product_compliance")
    op.drop_table("bom_item_alternates")
    op.drop_column("product_bom_items", "notes")
    op.drop_column("product_bom_items", "component_type")
    op.drop_column("product_bom_items", "reference_designator")
