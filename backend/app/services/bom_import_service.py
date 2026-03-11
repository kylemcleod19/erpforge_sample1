"""BOM CSV import service — parse, preview, and apply."""
import csv
import io
import logging
from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import Session

from app.models.product import Product, ProductBOMItem
from app.schemas.product import (
    BOMConflict,
    BOMImportApplyRequest,
    BOMImportApplyResponse,
    BOMImportPreviewResponse,
    BOMImportRow,
)

logger = logging.getLogger(__name__)

MAX_ROWS = 5000
REQUIRED_HEADERS = {"parent_sku", "child_sku", "quantity"}


def parse_bom_csv(content: bytes, db: Session) -> BOMImportPreviewResponse:
    errors: list[str] = []
    new_rows: list[BOMImportRow] = []
    conflicts: list[BOMConflict] = []

    try:
        text = content.decode("utf-8-sig")  # handle optional BOM in file
    except UnicodeDecodeError:
        return BOMImportPreviewResponse(
            new_rows=[], conflicts=[], errors=["File must be UTF-8 encoded"]
        )

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        return BOMImportPreviewResponse(
            new_rows=[], conflicts=[], errors=["CSV file is empty or has no headers"]
        )

    headers = {h.strip().lower() for h in reader.fieldnames}
    missing = REQUIRED_HEADERS - headers
    if missing:
        return BOMImportPreviewResponse(
            new_rows=[],
            conflicts=[],
            errors=[f"Missing required columns: {', '.join(sorted(missing))}"],
        )

    raw_rows: list[dict] = []
    for i, row in enumerate(reader, start=2):  # row 1 = header
        if i - 1 > MAX_ROWS:
            errors.append(f"File exceeds {MAX_ROWS} row limit; truncated at row {MAX_ROWS}")
            break
        raw_rows.append({"line": i, **row})

    if not raw_rows:
        return BOMImportPreviewResponse(new_rows=[], conflicts=[], errors=["CSV has no data rows"])

    # Collect all unique SKUs for batch lookup
    all_skus: set[str] = set()
    parsed: list[dict] = []
    for raw in raw_rows:
        parent_sku = (raw.get("parent_sku") or "").strip()
        child_sku = (raw.get("child_sku") or "").strip()
        qty_str = (raw.get("quantity") or "").strip()
        ref_des = (raw.get("ref_designator") or raw.get("reference_designator") or "").strip() or None

        if not parent_sku or not child_sku:
            errors.append(f"Row {raw['line']}: parent_sku and child_sku are required")
            continue
        try:
            qty = Decimal(qty_str)
            if qty <= 0:
                raise ValueError("quantity must be > 0")
        except (InvalidOperation, ValueError):
            errors.append(f"Row {raw['line']}: invalid quantity '{qty_str}'")
            continue

        all_skus.add(parent_sku)
        all_skus.add(child_sku)
        parsed.append({"parent_sku": parent_sku, "child_sku": child_sku, "quantity": qty, "ref_designator": ref_des})

    if not parsed:
        return BOMImportPreviewResponse(new_rows=[], conflicts=[], errors=errors)

    # Batch SKU lookup
    products = db.query(Product).filter(Product.sku.in_(list(all_skus))).all()
    sku_map: dict[str, Product] = {p.sku: p for p in products}

    unknown = all_skus - set(sku_map.keys())
    for sku in sorted(unknown):
        errors.append(f"Unknown SKU: '{sku}'")

    # Filter rows where both SKUs are known
    valid_parsed = [
        r for r in parsed
        if r["parent_sku"] in sku_map and r["child_sku"] in sku_map
    ]

    if not valid_parsed:
        return BOMImportPreviewResponse(new_rows=[], conflicts=[], errors=errors)

    # Load existing BOM items for all parent IDs in valid rows
    parent_ids = {sku_map[r["parent_sku"]].id for r in valid_parsed}
    existing_items = (
        db.query(ProductBOMItem)
        .filter(ProductBOMItem.parent_product_id.in_(list(parent_ids)))
        .all()
    )
    # Index: (parent_id, child_id) -> item
    existing_index: dict[tuple[int, int], ProductBOMItem] = {
        (item.parent_product_id, item.child_product_id): item
        for item in existing_items
    }

    for r in valid_parsed:
        parent = sku_map[r["parent_sku"]]
        child = sku_map[r["child_sku"]]
        key = (parent.id, child.id)

        if parent.id == child.id:
            errors.append(f"Row: {r['parent_sku']} cannot reference itself in BOM")
            continue

        row_obj = BOMImportRow(
            parent_sku=r["parent_sku"],
            child_sku=r["child_sku"],
            quantity=r["quantity"],
            ref_designator=r["ref_designator"],
            parent_product_id=parent.id,
            child_product_id=child.id,
        )

        if key in existing_index:
            existing = existing_index[key]
            conflicts.append(
                BOMConflict(
                    parent_sku=r["parent_sku"],
                    parent_product_id=parent.id,
                    child_sku=r["child_sku"],
                    child_product_id=child.id,
                    existing_quantity=existing.quantity,
                    existing_ref_designator=existing.reference_designator,
                    new_quantity=r["quantity"],
                    new_ref_designator=r["ref_designator"],
                )
            )
        else:
            new_rows.append(row_obj)

    return BOMImportPreviewResponse(new_rows=new_rows, conflicts=conflicts, errors=errors)


def apply_bom_import(request: BOMImportApplyRequest, db: Session) -> BOMImportApplyResponse:
    created = updated = skipped = 0

    # Collect SKUs for re-validation
    all_skus: set[str] = set()
    for row in request.rows:
        all_skus.add(row.parent_sku)
        all_skus.add(row.child_sku)

    products = db.query(Product).filter(Product.sku.in_(list(all_skus))).all()
    sku_map: dict[str, Product] = {p.sku: p for p in products}

    # Build upsert set: {(parent_sku, child_sku)}
    upsert_set: set[tuple[str, str]] = {
        (pair[0], pair[1]) for pair in request.upsert_pairs if len(pair) == 2
    }

    for row in request.rows:
        parent = sku_map.get(row.parent_sku)
        child = sku_map.get(row.child_sku)
        if not parent or not child:
            skipped += 1
            continue

        existing = (
            db.query(ProductBOMItem)
            .filter(
                ProductBOMItem.parent_product_id == parent.id,
                ProductBOMItem.child_product_id == child.id,
            )
            .first()
        )

        if existing:
            # This is a conflict row — only apply if in upsert_set
            if (row.parent_sku, row.child_sku) in upsert_set:
                existing.quantity = row.quantity
                existing.reference_designator = row.ref_designator
                updated += 1
            else:
                skipped += 1
        else:
            item = ProductBOMItem(
                parent_product_id=parent.id,
                child_product_id=child.id,
                quantity=row.quantity,
                reference_designator=row.ref_designator,
            )
            db.add(item)
            created += 1

    db.commit()
    logger.info("BOM import applied: created=%d updated=%d skipped=%d", created, updated, skipped)
    return BOMImportApplyResponse(created=created, updated=updated, skipped=skipped)
