from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    quote_id: Mapped[int | None] = mapped_column(ForeignKey("quotes.id"))
    status: Mapped[str] = mapped_column(String(50), default="pending")
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    line_items: Mapped[list["OrderLineItem"]] = relationship(
        "OrderLineItem", back_populates="order", cascade="all, delete-orphan"
    )
    quote: Mapped["Quote | None"] = relationship("Quote")


class OrderLineItem(Base):
    __tablename__ = "order_line_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)

    order: Mapped["Order"] = relationship("Order", back_populates="line_items")
    product: Mapped["Product"] = relationship("Product")


from app.models.quote import Quote  # noqa: E402, F401
from app.models.product import Product  # noqa: E402, F401
