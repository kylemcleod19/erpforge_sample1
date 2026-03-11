from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# ProductSpec
# ---------------------------------------------------------------------------

class ProductSpecBase(BaseModel):
    label: str
    url: str


class ProductSpecCreate(ProductSpecBase):
    pass


class ProductSpecOut(ProductSpecBase):
    id: int
    product_id: int

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# BOM items
# ---------------------------------------------------------------------------

class BOMItemBase(BaseModel):
    child_product_id: int
    quantity: Decimal
    unit_of_measure: str = "EA"
    # Phase 3 enrichment
    reference_designator: str | None = None
    component_type: str | None = None
    notes: str | None = None
    line_designator: str | None = None


class BOMItemCreate(BOMItemBase):
    pass


class BOMItemOut(BOMItemBase):
    id: int
    parent_product_id: int
    bom_revision_id: int | None = None
    child_product_name: str | None = None
    child_product_sku: str | None = None
    # Obsolete component warning returned on POST
    warnings: list[str] = []

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# BOM alternates
# ---------------------------------------------------------------------------

class BOMItemAlternateCreate(BaseModel):
    alternate_product_id: int
    priority: int = 1
    notes: str | None = None


class BOMItemAlternateOut(BOMItemAlternateCreate):
    id: int
    bom_item_id: int
    alternate_product_name: str | None = None
    alternate_product_sku: str | None = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# BOM revisions
# ---------------------------------------------------------------------------

class BOMRevisionCreate(BaseModel):
    revision_number: int
    notes: str | None = None


class BOMRevisionApprove(BaseModel):
    approved_by: str


class BOMRevisionOut(BaseModel):
    id: int
    product_id: int
    revision_number: int
    status: str
    notes: str | None = None
    created_at: datetime
    approved_by: str | None = None
    approved_at: datetime | None = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------

class ProductBase(BaseModel):
    sku: str
    name: str
    description: str | None = None
    unit_price: Decimal = Decimal("0")
    unit_cost: Decimal = Decimal("0")
    unit_of_measure: str = "EA"
    # Phase 1 enrichment
    category: str | None = None
    revision: int = 1
    lifecycle_status: str = "production"
    item_type: str = "finished_good"
    traceability_type: str = "none"
    compliance_required: bool = False


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    sku: str | None = None
    name: str | None = None
    description: str | None = None
    unit_price: Decimal | None = None
    unit_cost: Decimal | None = None
    unit_of_measure: str | None = None
    category: str | None = None
    revision: int | None = None
    lifecycle_status: str | None = None
    item_type: str | None = None
    traceability_type: str | None = None
    compliance_required: bool | None = None


class ProductOut(ProductBase):
    id: int
    created_at: datetime
    bom_items: list[BOMItemOut] = []
    specs: list[ProductSpecOut] = []

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Cost rollup
# ---------------------------------------------------------------------------

class CostNode(BaseModel):
    product_id: int
    sku: str
    name: str
    unit_cost: Decimal
    rolled_up_cost: Decimal
    children: list["CostNode"] = []

    model_config = {"from_attributes": True}


CostNode.model_rebuild()


# ---------------------------------------------------------------------------
# Compliance
# ---------------------------------------------------------------------------

class ProductComplianceCreate(BaseModel):
    scope: str
    cert_type: str
    cert_number: str | None = None
    issued_date: date | None = None
    expiry_date: date | None = None
    document_url: str | None = None
    notes: str | None = None


class ProductComplianceOut(ProductComplianceCreate):
    id: int
    product_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# BOM CSV Import
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# BOM CSV Import — Column Detection
# ---------------------------------------------------------------------------

class ColumnMapping(BaseModel):
    csv_column: str
    mapped_to: str | None = None


class ColumnDetectResponse(BaseModel):
    csv_columns: list[str]
    suggested_mappings: list[ColumnMapping]
    available_fields: list[dict]
    sample_rows: list[dict[str, str]]


# ---------------------------------------------------------------------------
# BOM CSV Import — Preview / Apply
# ---------------------------------------------------------------------------

class BOMImportRow(BaseModel):
    parent_sku: str
    child_sku: str
    quantity: Decimal
    ref_designator: str | None = None
    line_designator: str | None = None
    unit_of_measure: str | None = None
    component_type: str | None = None
    notes: str | None = None
    row_number: int | None = None
    row_errors: list[str] = []
    # Resolved IDs (filled in by service after SKU lookup)
    parent_product_id: int | None = None
    child_product_id: int | None = None


class BOMConflict(BaseModel):
    parent_sku: str
    parent_product_id: int
    child_sku: str
    child_product_id: int
    existing_quantity: Decimal
    existing_ref_designator: str | None
    new_quantity: Decimal
    new_ref_designator: str | None
    existing_line_designator: str | None = None
    new_line_designator: str | None = None
    existing_unit_of_measure: str | None = None
    new_unit_of_measure: str | None = None
    existing_component_type: str | None = None
    new_component_type: str | None = None
    existing_notes: str | None = None
    new_notes: str | None = None


class BOMImportPreviewResponse(BaseModel):
    new_rows: list[BOMImportRow]
    conflicts: list[BOMConflict]
    errors: list[str]
    column_mappings: list[ColumnMapping] = []


class BOMImportApplyRequest(BaseModel):
    rows: list[BOMImportRow]
    # List of [parent_sku, child_sku] pairs from conflicts to overwrite
    upsert_pairs: list[list[str]]


class BOMImportApplyResponse(BaseModel):
    created: int
    updated: int
    skipped: int
