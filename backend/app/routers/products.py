import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import verify_turnstile
from app.models.product import (
    BOMItemAlternate,
    BOMRevision,
    Product,
    ProductBOMItem,
    ProductCompliance,
    ProductSpec,
)
from app.schemas.product import (
    BOMImportApplyRequest,
    BOMImportApplyResponse,
    BOMImportPreviewResponse,
    BOMItemAlternateCreate,
    BOMItemAlternateOut,
    BOMItemCreate,
    BOMItemOut,
    BOMRevisionApprove,
    BOMRevisionCreate,
    BOMRevisionOut,
    ColumnDetectResponse,
    CostNode,
    ProductComplianceCreate,
    ProductComplianceOut,
    ProductCreate,
    ProductOut,
    ProductSpecCreate,
    ProductSpecOut,
    ProductUpdate,
)
from app.services.bom_import_service import (
    apply_bom_import,
    detect_columns,
    generate_template,
    parse_bom_csv,
)
from app.services.bom_service import compute_cost_rollup, get_bom_tree

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/products", tags=["products"])


def _enrich_bom_item(item: ProductBOMItem, warnings: list[str] | None = None) -> BOMItemOut:
    return BOMItemOut(
        id=item.id,
        parent_product_id=item.parent_product_id,
        child_product_id=item.child_product_id,
        quantity=item.quantity,
        unit_of_measure=item.unit_of_measure,
        bom_revision_id=item.bom_revision_id,
        reference_designator=item.reference_designator,
        component_type=item.component_type,
        notes=item.notes,
        line_designator=item.line_designator,
        child_product_name=item.child_product.name if item.child_product else None,
        child_product_sku=item.child_product.sku if item.child_product else None,
        warnings=warnings or [],
    )


# ---------------------------------------------------------------------------
# Products CRUD
# ---------------------------------------------------------------------------

@router.get("", response_model=list[ProductOut])
def list_products(
    item_type: list[str] | None = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Product)
    if item_type:
        q = q.filter(Product.item_type.in_(item_type))
    return q.order_by(Product.sku).all()


@router.post("", response_model=ProductOut, status_code=201)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    existing = db.query(Product).filter(Product.sku == payload.sku).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"SKU '{payload.sku}' already exists")
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


# ---------------------------------------------------------------------------
# BOM CSV Import (must be declared before /{product_id} routes)
# ---------------------------------------------------------------------------

@router.post("/bom/import/detect-columns", response_model=ColumnDetectResponse)
async def bom_import_detect_columns(file: UploadFile = File(...)):
    content = await file.read()
    return detect_columns(content)


@router.post("/bom/import/preview", response_model=BOMImportPreviewResponse, dependencies=[Depends(verify_turnstile)])
async def bom_import_preview(
    file: UploadFile = File(...),
    column_mappings: str | None = Form(None),
    db: Session = Depends(get_db),
):
    content = await file.read()
    overrides: dict[str, str] | None = None
    if column_mappings:
        try:
            overrides = json.loads(column_mappings)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid column_mappings JSON")
    return parse_bom_csv(content, db, column_overrides=overrides)


@router.post("/bom/import/apply", response_model=BOMImportApplyResponse, dependencies=[Depends(verify_turnstile)])
def bom_import_apply(
    payload: BOMImportApplyRequest,
    db: Session = Depends(get_db),
):
    return apply_bom_import(payload, db)


@router.get("/bom/import/template")
def bom_import_template(type: str = Query("pcba", pattern="^(pcba|mechanical)$")):
    csv_content = generate_template(type)
    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="bom_template_{type}.csv"'},
    )


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/{product_id}", response_model=ProductOut)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()


# ---------------------------------------------------------------------------
# BOM items
# ---------------------------------------------------------------------------

@router.get("/{product_id}/bom", response_model=list[BOMItemOut])
def list_bom(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return [_enrich_bom_item(item) for item in product.bom_items]


@router.post("/{product_id}/bom", response_model=BOMItemOut, status_code=201)
def add_bom_item(
    product_id: int,
    payload: BOMItemCreate,
    revision_id: int | None = Query(None, description="Associate with a specific BOM revision"),
    db: Session = Depends(get_db),
):
    if not db.get(Product, product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    child = db.get(Product, payload.child_product_id)
    if not child:
        raise HTTPException(status_code=404, detail="Child product not found")
    if product_id == payload.child_product_id:
        raise HTTPException(status_code=400, detail="A product cannot reference itself in BOM")

    if revision_id is not None:
        rev = db.query(BOMRevision).filter(
            BOMRevision.id == revision_id,
            BOMRevision.product_id == product_id,
        ).first()
        if not rev:
            raise HTTPException(status_code=404, detail="BOM revision not found for this product")

    item = ProductBOMItem(
        parent_product_id=product_id,
        bom_revision_id=revision_id,
        **payload.model_dump(),
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    warnings: list[str] = []
    if child.lifecycle_status == "end_of_life":
        warnings.append(
            f"Component '{child.sku} — {child.name}' is end-of-life. "
            "Review before using in production BOM."
        )

    return _enrich_bom_item(item, warnings)


@router.delete("/{product_id}/bom/{bom_item_id}", status_code=204)
def remove_bom_item(product_id: int, bom_item_id: int, db: Session = Depends(get_db)):
    item = db.query(ProductBOMItem).filter(
        ProductBOMItem.id == bom_item_id,
        ProductBOMItem.parent_product_id == product_id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="BOM item not found")
    db.delete(item)
    db.commit()


# ---------------------------------------------------------------------------
# BOM alternates (Phase 3)
# ---------------------------------------------------------------------------

@router.get("/{product_id}/bom/{bom_item_id}/alternates", response_model=list[BOMItemAlternateOut])
def list_alternates(product_id: int, bom_item_id: int, db: Session = Depends(get_db)):
    item = db.query(ProductBOMItem).filter(
        ProductBOMItem.id == bom_item_id,
        ProductBOMItem.parent_product_id == product_id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="BOM item not found")
    return [
        BOMItemAlternateOut(
            id=a.id,
            bom_item_id=a.bom_item_id,
            alternate_product_id=a.alternate_product_id,
            priority=a.priority,
            notes=a.notes,
            alternate_product_name=a.alternate_product.name if a.alternate_product else None,
            alternate_product_sku=a.alternate_product.sku if a.alternate_product else None,
        )
        for a in item.alternates
    ]


@router.post("/{product_id}/bom/{bom_item_id}/alternates", response_model=BOMItemAlternateOut, status_code=201)
def add_alternate(
    product_id: int,
    bom_item_id: int,
    payload: BOMItemAlternateCreate,
    db: Session = Depends(get_db),
):
    item = db.query(ProductBOMItem).filter(
        ProductBOMItem.id == bom_item_id,
        ProductBOMItem.parent_product_id == product_id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="BOM item not found")
    alt_product = db.get(Product, payload.alternate_product_id)
    if not alt_product:
        raise HTTPException(status_code=404, detail="Alternate product not found")

    alt = BOMItemAlternate(bom_item_id=bom_item_id, **payload.model_dump())
    db.add(alt)
    db.commit()
    db.refresh(alt)
    return BOMItemAlternateOut(
        id=alt.id,
        bom_item_id=alt.bom_item_id,
        alternate_product_id=alt.alternate_product_id,
        priority=alt.priority,
        notes=alt.notes,
        alternate_product_name=alt_product.name,
        alternate_product_sku=alt_product.sku,
    )


@router.delete("/{product_id}/bom/{bom_item_id}/alternates/{alt_id}", status_code=204)
def remove_alternate(product_id: int, bom_item_id: int, alt_id: int, db: Session = Depends(get_db)):
    item = db.query(ProductBOMItem).filter(
        ProductBOMItem.id == bom_item_id,
        ProductBOMItem.parent_product_id == product_id,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="BOM item not found")
    alt = db.query(BOMItemAlternate).filter(
        BOMItemAlternate.id == alt_id,
        BOMItemAlternate.bom_item_id == bom_item_id,
    ).first()
    if not alt:
        raise HTTPException(status_code=404, detail="Alternate not found")
    db.delete(alt)
    db.commit()


# ---------------------------------------------------------------------------
# BOM revisions (Phase 2)
# ---------------------------------------------------------------------------

@router.get("/{product_id}/bom-revisions", response_model=list[BOMRevisionOut])
def list_bom_revisions(product_id: int, db: Session = Depends(get_db)):
    if not db.get(Product, product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    return (
        db.query(BOMRevision)
        .filter(BOMRevision.product_id == product_id)
        .order_by(BOMRevision.revision_number)
        .all()
    )


@router.post("/{product_id}/bom-revisions", response_model=BOMRevisionOut, status_code=201)
def create_bom_revision(product_id: int, payload: BOMRevisionCreate, db: Session = Depends(get_db)):
    if not db.get(Product, product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    existing = db.query(BOMRevision).filter(
        BOMRevision.product_id == product_id,
        BOMRevision.revision_number == payload.revision_number,
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Revision {payload.revision_number} already exists for this product",
        )
    rev = BOMRevision(product_id=product_id, **payload.model_dump())
    db.add(rev)
    db.commit()
    db.refresh(rev)
    return rev


@router.patch("/{product_id}/bom-revisions/{rev_id}/approve", response_model=BOMRevisionOut)
def approve_bom_revision(
    product_id: int,
    rev_id: int,
    payload: BOMRevisionApprove,
    db: Session = Depends(get_db),
):
    rev = db.query(BOMRevision).filter(
        BOMRevision.id == rev_id,
        BOMRevision.product_id == product_id,
    ).first()
    if not rev:
        raise HTTPException(status_code=404, detail="BOM revision not found")
    if rev.status == "approved":
        raise HTTPException(status_code=400, detail="Revision is already approved")

    # Supersede any previously approved revision for this product
    db.query(BOMRevision).filter(
        BOMRevision.product_id == product_id,
        BOMRevision.status == "approved",
    ).update({"status": "superseded"})

    rev.status = "approved"
    rev.approved_by = payload.approved_by
    rev.approved_at = datetime.utcnow()
    db.commit()
    db.refresh(rev)
    return rev


@router.get("/{product_id}/bom-revisions/{rev_id}/bom", response_model=list[BOMItemOut])
def list_bom_for_revision(product_id: int, rev_id: int, db: Session = Depends(get_db)):
    rev = db.query(BOMRevision).filter(
        BOMRevision.id == rev_id,
        BOMRevision.product_id == product_id,
    ).first()
    if not rev:
        raise HTTPException(status_code=404, detail="BOM revision not found")
    items = (
        db.query(ProductBOMItem)
        .filter(ProductBOMItem.bom_revision_id == rev_id)
        .all()
    )
    return [_enrich_bom_item(item) for item in items]


# ---------------------------------------------------------------------------
# Specs
# ---------------------------------------------------------------------------

@router.get("/{product_id}/specs", response_model=list[ProductSpecOut])
def list_specs(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product.specs


@router.post("/{product_id}/specs", response_model=ProductSpecOut, status_code=201)
def add_spec(product_id: int, payload: ProductSpecCreate, db: Session = Depends(get_db)):
    if not db.get(Product, product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    spec = ProductSpec(product_id=product_id, **payload.model_dump())
    db.add(spec)
    db.commit()
    db.refresh(spec)
    return spec


@router.delete("/{product_id}/specs/{spec_id}", status_code=204)
def remove_spec(product_id: int, spec_id: int, db: Session = Depends(get_db)):
    spec = db.query(ProductSpec).filter(
        ProductSpec.id == spec_id,
        ProductSpec.product_id == product_id,
    ).first()
    if not spec:
        raise HTTPException(status_code=404, detail="Spec not found")
    db.delete(spec)
    db.commit()


# ---------------------------------------------------------------------------
# Compliance (Phase 4)
# ---------------------------------------------------------------------------

@router.get("/{product_id}/compliance", response_model=list[ProductComplianceOut])
def list_compliance(product_id: int, db: Session = Depends(get_db)):
    if not db.get(Product, product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    return (
        db.query(ProductCompliance)
        .filter(ProductCompliance.product_id == product_id)
        .order_by(ProductCompliance.cert_type)
        .all()
    )


@router.post("/{product_id}/compliance", response_model=ProductComplianceOut, status_code=201)
def add_compliance(product_id: int, payload: ProductComplianceCreate, db: Session = Depends(get_db)):
    if not db.get(Product, product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    record = ProductCompliance(product_id=product_id, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.delete("/{product_id}/compliance/{cert_id}", status_code=204)
def remove_compliance(product_id: int, cert_id: int, db: Session = Depends(get_db)):
    record = db.query(ProductCompliance).filter(
        ProductCompliance.id == cert_id,
        ProductCompliance.product_id == product_id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Compliance record not found")
    db.delete(record)
    db.commit()


# ---------------------------------------------------------------------------
# Cost rollup
# ---------------------------------------------------------------------------

@router.get("/{product_id}/cost", response_model=CostNode)
def get_cost_rollup(product_id: int, db: Session = Depends(get_db)):
    if not db.get(Product, product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    try:
        return compute_cost_rollup(product_id, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
