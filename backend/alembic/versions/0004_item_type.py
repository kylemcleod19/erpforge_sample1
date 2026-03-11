"""replace make_buy with item_type

Revision ID: 0004
Revises: 0003
Create Date: 2026-03-10

"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add item_type as nullable first
    op.add_column("products", sa.Column("item_type", sa.String(30), nullable=True))

    # Migrate data from make_buy
    op.execute("""
        UPDATE products SET item_type = CASE
            WHEN make_buy = 'buy'    THEN 'component'
            WHEN make_buy = 'make'   THEN 'assembly'
            WHEN make_buy = 'either' THEN 'assembly'
            ELSE 'finished_good'
        END
    """)

    # Make NOT NULL now that data is populated
    op.alter_column("products", "item_type", nullable=False)

    # Drop old column
    op.drop_column("products", "make_buy")


def downgrade() -> None:
    op.add_column("products", sa.Column("make_buy", sa.String(10), nullable=True))

    op.execute("""
        UPDATE products SET make_buy = CASE
            WHEN item_type = 'component'    THEN 'buy'
            WHEN item_type = 'raw_material' THEN 'buy'
            WHEN item_type = 'assembly'     THEN 'make'
            WHEN item_type = 'finished_good' THEN 'make'
            ELSE 'either'
        END
    """)

    op.alter_column("products", "make_buy", nullable=False)
    op.drop_column("products", "item_type")
