"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-03-09

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sku", sa.String(100), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("unit_price", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("unit_cost", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("unit_of_measure", sa.String(50), nullable=False, server_default="EA"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sku"),
    )

    op.create_table(
        "product_bom_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("parent_product_id", sa.Integer(), nullable=False),
        sa.Column("child_product_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(14, 4), nullable=False),
        sa.Column("unit_of_measure", sa.String(50), nullable=False, server_default="EA"),
        sa.ForeignKeyConstraint(["parent_product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["child_product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "product_specs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "quotes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_name", sa.String(255), nullable=False),
        sa.Column("customer_email", sa.String(255), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "quote_line_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("quote_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(14, 4), nullable=False),
        sa.Column("unit_price", sa.Numeric(14, 4), nullable=False),
        sa.Column("lead_time_days", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["quote_id"], ["quotes.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("quote_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["quote_id"], ["quotes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "order_line_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(14, 4), nullable=False),
        sa.Column("unit_price", sa.Numeric(14, 4), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "inventory_balances",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity_on_hand", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id"),
    )

    op.create_table(
        "inventory_reservations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity_reserved", sa.Numeric(14, 4), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "purchase_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity_needed", sa.Numeric(14, 4), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "work_stations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sequence", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "product_routings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("station_id", sa.Integer(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["station_id"], ["work_stations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "work_orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Numeric(14, 4), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="queued"),
        sa.Column("current_station_sequence", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "work_order_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("work_order_id", sa.Integer(), nullable=False),
        sa.Column("station_id", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("operator", sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(["work_order_id"], ["work_orders.id"]),
        sa.ForeignKeyConstraint(["station_id"], ["work_stations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "shipments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("shipping_account_number", sa.String(100), nullable=True),
        sa.Column("carrier", sa.String(100), nullable=True),
        sa.Column("tracking_number", sa.String(255), nullable=True),
        sa.Column("shipped_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("shipment_id", sa.Integer(), nullable=False),
        sa.Column("invoice_number", sa.String(100), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("subtotal", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("tax_amount", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("total_amount", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["shipment_id"], ["shipments.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invoice_number"),
    )

    op.create_table(
        "invoice_line_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("invoice_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("quantity", sa.Numeric(14, 4), nullable=False),
        sa.Column("unit_price", sa.Numeric(14, 4), nullable=False),
        sa.Column("subtotal", sa.Numeric(14, 4), nullable=False),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("invoice_line_items")
    op.drop_table("invoices")
    op.drop_table("shipments")
    op.drop_table("work_order_logs")
    op.drop_table("work_orders")
    op.drop_table("product_routings")
    op.drop_table("work_stations")
    op.drop_table("purchase_requests")
    op.drop_table("inventory_reservations")
    op.drop_table("inventory_balances")
    op.drop_table("order_line_items")
    op.drop_table("orders")
    op.drop_table("quote_line_items")
    op.drop_table("quotes")
    op.drop_table("product_specs")
    op.drop_table("product_bom_items")
    op.drop_table("products")
