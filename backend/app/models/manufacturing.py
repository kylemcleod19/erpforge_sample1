from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class WorkStation(Base):
    __tablename__ = "work_stations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    sequence: Mapped[int] = mapped_column(Integer, default=0)

    routings: Mapped[list["ProductRouting"]] = relationship(
        "ProductRouting", back_populates="station"
    )


class ProductRouting(Base):
    __tablename__ = "product_routings"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    station_id: Mapped[int] = mapped_column(ForeignKey("work_stations.id"), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)

    product: Mapped["Product"] = relationship("Product")
    station: Mapped["WorkStation"] = relationship("WorkStation", back_populates="routings")


class WorkOrder(Base):
    __tablename__ = "work_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="queued")
    current_station_sequence: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    # Phase 2: snapshot the approved BOM revision at work order creation time
    bom_revision_id: Mapped[int | None] = mapped_column(
        ForeignKey("bom_revisions.id"), nullable=True
    )

    order: Mapped["Order"] = relationship("Order")
    product: Mapped["Product"] = relationship("Product")
    logs: Mapped[list["WorkOrderLog"]] = relationship(
        "WorkOrderLog", back_populates="work_order", cascade="all, delete-orphan"
    )


class WorkOrderLog(Base):
    __tablename__ = "work_order_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    work_order_id: Mapped[int] = mapped_column(ForeignKey("work_orders.id"), nullable=False)
    station_id: Mapped[int] = mapped_column(ForeignKey("work_stations.id"), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    notes: Mapped[str | None] = mapped_column(Text)
    operator: Mapped[str | None] = mapped_column(String(255))

    work_order: Mapped["WorkOrder"] = relationship("WorkOrder", back_populates="logs")
    station: Mapped["WorkStation"] = relationship("WorkStation")


from app.models.product import Product  # noqa: E402, F401
from app.models.order import Order  # noqa: E402, F401
