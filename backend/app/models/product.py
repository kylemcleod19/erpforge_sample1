from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=0)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=0)
    unit_of_measure: Mapped[str] = mapped_column(String(50), default="EA")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    bom_items: Mapped[list["ProductBOMItem"]] = relationship(
        "ProductBOMItem", foreign_keys="ProductBOMItem.parent_product_id", back_populates="parent_product", cascade="all, delete-orphan"
    )
    specs: Mapped[list["ProductSpec"]] = relationship(
        "ProductSpec", back_populates="product", cascade="all, delete-orphan"
    )


class ProductBOMItem(Base):
    __tablename__ = "product_bom_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    child_product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(50), default="EA")

    parent_product: Mapped["Product"] = relationship(
        "Product", foreign_keys=[parent_product_id], back_populates="bom_items"
    )
    child_product: Mapped["Product"] = relationship(
        "Product", foreign_keys=[child_product_id]
    )


class ProductSpec(Base):
    __tablename__ = "product_specs"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)

    product: Mapped["Product"] = relationship("Product", back_populates="specs")
