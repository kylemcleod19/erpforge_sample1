from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    shipment_id: Mapped[int] = mapped_column(ForeignKey("shipments.id"), nullable=False)
    invoice_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=0)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    order: Mapped["Order"] = relationship("Order")
    shipment: Mapped["Shipment"] = relationship("Shipment")
    line_items: Mapped[list["InvoiceLineItem"]] = relationship(
        "InvoiceLineItem", back_populates="invoice", cascade="all, delete-orphan"
    )


class InvoiceLineItem(Base):
    __tablename__ = "invoice_line_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), nullable=False)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)

    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="line_items")
    product: Mapped["Product | None"] = relationship("Product")


from app.models.order import Order  # noqa: E402, F401
from app.models.shipping import Shipment  # noqa: E402, F401
from app.models.product import Product  # noqa: E402, F401
