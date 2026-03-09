import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.product import Product, ProductBOMItem, ProductSpec
from app.schemas.product import (
    BOMItemCreate,
    BOMItemOut,
    CostNode,
    ProductCreate,
    ProductOut,
    ProductSpecCreate,
    ProductSpecOut,
    ProductUpdate,
)
from app.services.bom_service import compute_cost_rollup, get_bom_tree

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/products", tags=["products"])


def _enrich_bom_item(item: ProductBOMItem) -> BOMItemOut:
    return BOMItemOut(
        id=item.id,
        parent_product_id=item.parent_product_id,
        child_product_id=item.child_product_id,
        quantity=item.quantity,
        unit_of_measure=item.unit_of_measure,
        child_product_name=item.child_product.name if item.child_product else None,
        child_product_sku=item.child_product.sku if item.child_product else None,
    )


@router.get("", response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db)):
    return db.query(Product).order_by(Product.sku).all()


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


# --- BOM ---

@router.get("/{product_id}/bom", response_model=list[BOMItemOut])
def list_bom(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return [_enrich_bom_item(item) for item in product.bom_items]


@router.post("/{product_id}/bom", response_model=BOMItemOut, status_code=201)
def add_bom_item(product_id: int, payload: BOMItemCreate, db: Session = Depends(get_db)):
    if not db.get(Product, product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    if not db.get(Product, payload.child_product_id):
        raise HTTPException(status_code=404, detail="Child product not found")
    if product_id == payload.child_product_id:
        raise HTTPException(status_code=400, detail="A product cannot reference itself in BOM")

    item = ProductBOMItem(parent_product_id=product_id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return _enrich_bom_item(item)


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


# --- Specs ---

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


# --- Cost rollup ---

@router.get("/{product_id}/cost", response_model=CostNode)
def get_cost_rollup(product_id: int, db: Session = Depends(get_db)):
    if not db.get(Product, product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    try:
        return compute_cost_rollup(product_id, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
