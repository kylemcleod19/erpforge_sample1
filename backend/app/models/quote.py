from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Quote(Base):
    __tablename__ = "quotes"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_email: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="draft")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=datetime.utcnow)

    line_items: Mapped[list["QuoteLineItem"]] = relationship(
        "QuoteLineItem", back_populates="quote", cascade="all, delete-orphan"
    )


class QuoteLineItem(Base):
    __tablename__ = "quote_line_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    quote_id: Mapped[int] = mapped_column(ForeignKey("quotes.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    lead_time_days: Mapped[int | None] = mapped_column()

    quote: Mapped["Quote"] = relationship("Quote", back_populates="line_items")
    product: Mapped["Product"] = relationship("Product")

    @property
    def subtotal(self) -> Decimal:
        return self.quantity * self.unit_price


# avoid circular import
from app.models.product import Product  # noqa: E402, F401
