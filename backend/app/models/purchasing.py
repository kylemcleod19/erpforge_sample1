from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal

from app.database import Base


class PurchaseRequest(Base):
    __tablename__ = "purchase_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity_needed: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    order: Mapped["Order"] = relationship("Order")
    product: Mapped["Product"] = relationship("Product")


from app.models.order import Order  # noqa: E402, F401
from app.models.product import Product  # noqa: E402, F401
