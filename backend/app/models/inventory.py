from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class InventoryBalance(Base):
    __tablename__ = "inventory_balances"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), unique=True, nullable=False)
    quantity_on_hand: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=0)

    product: Mapped["Product"] = relationship("Product")


class InventoryReservation(Base):
    __tablename__ = "inventory_reservations"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity_reserved: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    product: Mapped["Product"] = relationship("Product")
    order: Mapped["Order"] = relationship("Order")


from app.models.product import Product  # noqa: E402, F401
from app.models.order import Order  # noqa: E402, F401
