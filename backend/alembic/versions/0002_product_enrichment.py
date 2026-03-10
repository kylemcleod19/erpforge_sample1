"""product enrichment and bom revisions

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-09
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Phase 1: product enrichment columns
    op.add_column("products", sa.Column("category", sa.String(100), nullable=True))
    op.add_column("products", sa.Column("revision", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("products", sa.Column("lifecycle_status", sa.String(30), nullable=False, server_default="production"))
    op.add_column("products", sa.Column("make_buy", sa.String(10), nullable=False, server_default="buy"))
    op.add_column("products", sa.Column("traceability_type", sa.String(20), nullable=False, server_default="none"))
    op.add_column("products", sa.Column("compliance_required", sa.Boolean(), nullable=False, server_default="false"))

    # Phase 2: bom_revisions table
    op.create_table(
        "bom_revisions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("approved_by", sa.String(100), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id", "revision_number", name="uq_bom_revisions_product_rev"),
    )

    # Phase 2: add bom_revision_id FK to product_bom_items
    op.add_column("product_bom_items", sa.Column("bom_revision_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_bom_items_revision",
        "product_bom_items", "bom_revisions",
        ["bom_revision_id"], ["id"],
    )

    # Phase 2: add bom_revision_id FK to work_orders
    op.add_column("work_orders", sa.Column("bom_revision_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_work_orders_bom_revision",
        "work_orders", "bom_revisions",
        ["bom_revision_id"], ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_work_orders_bom_revision", "work_orders", type_="foreignkey")
    op.drop_column("work_orders", "bom_revision_id")

    op.drop_constraint("fk_bom_items_revision", "product_bom_items", type_="foreignkey")
    op.drop_column("product_bom_items", "bom_revision_id")

    op.drop_table("bom_revisions")

    op.drop_column("products", "compliance_required")
    op.drop_column("products", "traceability_type")
    op.drop_column("products", "make_buy")
    op.drop_column("products", "lifecycle_status")
    op.drop_column("products", "revision")
    op.drop_column("products", "category")
