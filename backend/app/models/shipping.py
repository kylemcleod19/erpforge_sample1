from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Shipment(Base):
    __tablename__ = "shipments"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    shipping_account_number: Mapped[str | None] = mapped_column(String(100))
    carrier: Mapped[str | None] = mapped_column(String(100))
    tracking_number: Mapped[str | None] = mapped_column(String(255))
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime)
    notes: Mapped[str | None] = mapped_column(Text)

    order: Mapped["Order"] = relationship("Order")


from app.models.order import Order  # noqa: E402, F401
