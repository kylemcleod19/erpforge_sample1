from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
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

    # Phase 1 enrichment
    category: Mapped[str | None] = mapped_column(String(100))
    revision: Mapped[int] = mapped_column(Integer, default=1)
    lifecycle_status: Mapped[str] = mapped_column(String(30), default="production")
    make_buy: Mapped[str] = mapped_column(String(10), default="buy")
    traceability_type: Mapped[str] = mapped_column(String(20), default="none")
    compliance_required: Mapped[bool] = mapped_column(Boolean, default=False)

    bom_items: Mapped[list["ProductBOMItem"]] = relationship(
        "ProductBOMItem", foreign_keys="ProductBOMItem.parent_product_id",
        back_populates="parent_product", cascade="all, delete-orphan",
    )
    specs: Mapped[list["ProductSpec"]] = relationship(
        "ProductSpec", back_populates="product", cascade="all, delete-orphan",
    )
    bom_revisions: Mapped[list["BOMRevision"]] = relationship(
        "BOMRevision", back_populates="product", cascade="all, delete-orphan",
    )
    compliance_records: Mapped[list["ProductCompliance"]] = relationship(
        "ProductCompliance", back_populates="product", cascade="all, delete-orphan",
    )


class BOMRevision(Base):
    __tablename__ = "bom_revisions"
    __table_args__ = (
        UniqueConstraint("product_id", "revision_number", name="uq_bom_revisions_product_rev"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    approved_by: Mapped[str | None] = mapped_column(String(100))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime)

    product: Mapped["Product"] = relationship("Product", back_populates="bom_revisions")
    bom_items: Mapped[list["ProductBOMItem"]] = relationship(
        "ProductBOMItem", back_populates="bom_revision",
    )


class ProductBOMItem(Base):
    __tablename__ = "product_bom_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    child_product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(50), default="EA")

    # Phase 2: revision association
    bom_revision_id: Mapped[int | None] = mapped_column(
        ForeignKey("bom_revisions.id"), nullable=True
    )

    # Phase 3: line item enrichment
    reference_designator: Mapped[str | None] = mapped_column(String(50))
    component_type: Mapped[str | None] = mapped_column(String(30))
    notes: Mapped[str | None] = mapped_column(Text)

    parent_product: Mapped["Product"] = relationship(
        "Product", foreign_keys=[parent_product_id], back_populates="bom_items",
    )
    child_product: Mapped["Product"] = relationship(
        "Product", foreign_keys=[child_product_id],
    )
    bom_revision: Mapped["BOMRevision | None"] = relationship(
        "BOMRevision", back_populates="bom_items",
    )
    alternates: Mapped[list["BOMItemAlternate"]] = relationship(
        "BOMItemAlternate", back_populates="bom_item", cascade="all, delete-orphan",
    )


class BOMItemAlternate(Base):
    __tablename__ = "bom_item_alternates"

    id: Mapped[int] = mapped_column(primary_key=True)
    bom_item_id: Mapped[int] = mapped_column(
        ForeignKey("product_bom_items.id", ondelete="CASCADE"), nullable=False
    )
    alternate_product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=1)
    notes: Mapped[str | None] = mapped_column(Text)

    bom_item: Mapped["ProductBOMItem"] = relationship("ProductBOMItem", back_populates="alternates")
    alternate_product: Mapped["Product"] = relationship(
        "Product", foreign_keys=[alternate_product_id],
    )


class ProductSpec(Base):
    __tablename__ = "product_specs"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)

    product: Mapped["Product"] = relationship("Product", back_populates="specs")


class ProductCompliance(Base):
    __tablename__ = "product_compliance"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False
    )
    scope: Mapped[str] = mapped_column(String(20), nullable=False)
    cert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    cert_number: Mapped[str | None] = mapped_column(String(100))
    issued_date: Mapped[date | None] = mapped_column(Date)
    expiry_date: Mapped[date | None] = mapped_column(Date)
    document_url: Mapped[str | None] = mapped_column(String(2048))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    product: Mapped["Product"] = relationship("Product", back_populates="compliance_records")
