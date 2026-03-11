"""BOM CSV import service — detect columns, parse, preview, and apply."""
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
    ColumnDetectResponse,
    ColumnMapping,
)

logger = logging.getLogger(__name__)

MAX_ROWS = 5000

# ---------------------------------------------------------------------------
# Column alias registry
# ---------------------------------------------------------------------------

COLUMN_ALIASES: dict[str, list[str]] = {
    "parent_sku": [
        "parent_sku", "parent_part", "parent", "assembly",
        "assembly_sku", "parent_pn", "parent_part_number",
    ],
    "child_sku": [
        "child_sku", "child_part", "component", "component_sku",
        "child_pn", "part_number", "child_part_number",
    ],
    "quantity": [
        "quantity", "qty", "count", "qty_per", "quantity_per",
    ],
    "ref_designator": [
        "ref_designator", "reference_designator", "ref_des", "refdes",
    ],
    "line_designator": [
        "line_designator", "item_number", "line_number", "find_number",
        "item_no", "line_no", "find_no", "bubble_number",
    ],
    "unit_of_measure": [
        "unit_of_measure", "uom", "unit",
    ],
    "component_type": [
        "component_type", "comp_type", "type", "bom_type",
    ],
    "notes": [
        "notes", "comments", "remark", "remarks",
    ],
}

AVAILABLE_FIELDS = [
    {"field": "parent_sku", "description": "Parent assembly SKU/part number", "required": True},
    {"field": "child_sku", "description": "Child component SKU/part number", "required": True},
    {"field": "quantity", "description": "Quantity per assembly", "required": True},
    {"field": "ref_designator", "description": "Reference designator (e.g. R1, C4 for PCBA)", "required": False},
    {"field": "line_designator", "description": "Find/item/line number (e.g. for mechanical BOMs)", "required": False},
    {"field": "unit_of_measure", "description": "Unit of measure (EA, KG, M, etc.)", "required": False},
    {"field": "component_type", "description": "Component type (material, electronic, subassembly, etc.)", "required": False},
    {"field": "notes", "description": "Notes or comments", "required": False},
]

# Build a reverse lookup: normalised alias -> field name
_ALIAS_LOOKUP: dict[str, str] = {}
for _field, _aliases in COLUMN_ALIASES.items():
    for _alias in _aliases:
        _ALIAS_LOOKUP[_alias.lower().strip()] = _field


def _normalise(header: str) -> str:
    """Normalise a CSV header for alias matching."""
    return header.lower().strip().replace(" ", "_").replace("-", "_")


# ---------------------------------------------------------------------------
# Detect columns (Step 1 of three-step flow)
# ---------------------------------------------------------------------------

def detect_columns(content: bytes) -> ColumnDetectResponse:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return ColumnDetectResponse(
            csv_columns=[],
            suggested_mappings=[],
            available_fields=AVAILABLE_FIELDS,
            sample_rows=[],
        )

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        return ColumnDetectResponse(
            csv_columns=[],
            suggested_mappings=[],
            available_fields=AVAILABLE_FIELDS,
            sample_rows=[],
        )

    csv_columns = [h.strip() for h in reader.fieldnames]

    # Auto-map
    used_fields: set[str] = set()
    mappings: list[ColumnMapping] = []
    for col in csv_columns:
        norm = _normalise(col)
        matched = _ALIAS_LOOKUP.get(norm)
        if matched and matched not in used_fields:
            mappings.append(ColumnMapping(csv_column=col, mapped_to=matched))
            used_fields.add(matched)
        else:
            mappings.append(ColumnMapping(csv_column=col, mapped_to=None))

    # Sample rows (up to 5)
    sample_rows: list[dict[str, str]] = []
    for i, row in enumerate(reader):
        if i >= 5:
            break
        sample_rows.append({k.strip(): (v or "").strip() for k, v in row.items()})

    return ColumnDetectResponse(
        csv_columns=csv_columns,
        suggested_mappings=mappings,
        available_fields=AVAILABLE_FIELDS,
        sample_rows=sample_rows,
    )


# ---------------------------------------------------------------------------
# Parse CSV with optional column overrides (Step 2)
# ---------------------------------------------------------------------------

def _build_column_map(
    csv_columns: list[str],
    column_overrides: dict[str, str] | None = None,
) -> tuple[dict[str, str], list[ColumnMapping]]:
    """Return (csv_col -> field_name) mapping dict and ColumnMapping list."""
    col_map: dict[str, str] = {}
    mappings: list[ColumnMapping] = []

    if column_overrides:
        # User-provided overrides: csv_column -> field_name
        for csv_col, field in column_overrides.items():
            if field:
                col_map[csv_col.strip()] = field
                mappings.append(ColumnMapping(csv_column=csv_col.strip(), mapped_to=field))
            else:
                mappings.append(ColumnMapping(csv_column=csv_col.strip(), mapped_to=None))
    else:
        # Auto-detect
        used: set[str] = set()
        for col in csv_columns:
            norm = _normalise(col)
            matched = _ALIAS_LOOKUP.get(norm)
            if matched and matched not in used:
                col_map[col.strip()] = matched
                used.add(matched)
                mappings.append(ColumnMapping(csv_column=col.strip(), mapped_to=matched))
            else:
                mappings.append(ColumnMapping(csv_column=col.strip(), mapped_to=None))

    return col_map, mappings


def _get_field(row: dict, col_map: dict[str, str], field_name: str) -> str | None:
    """Extract a field value from a CSV row using the column mapping."""
    for csv_col, mapped in col_map.items():
        if mapped == field_name:
            val = (row.get(csv_col) or "").strip()
            return val if val else None
    return None


def parse_bom_csv(
    content: bytes,
    db: Session,
    column_overrides: dict[str, str] | None = None,
) -> BOMImportPreviewResponse:
    errors: list[str] = []
    new_rows: list[BOMImportRow] = []
    conflicts: list[BOMConflict] = []

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return BOMImportPreviewResponse(
            new_rows=[], conflicts=[], errors=["File must be UTF-8 encoded"]
        )

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        return BOMImportPreviewResponse(
            new_rows=[], conflicts=[], errors=["CSV file is empty or has no headers"]
        )

    csv_columns = [h.strip() for h in reader.fieldnames]
    col_map, column_mappings = _build_column_map(csv_columns, column_overrides)

    # Validate required fields are mapped
    mapped_fields = set(col_map.values())
    required = {"parent_sku", "child_sku", "quantity"}
    missing = required - mapped_fields
    if missing:
        return BOMImportPreviewResponse(
            new_rows=[],
            conflicts=[],
            errors=[f"Missing required column mappings: {', '.join(sorted(missing))}"],
            column_mappings=column_mappings,
        )

    raw_rows: list[tuple[int, dict]] = []
    for i, row in enumerate(reader, start=2):
        if i - 1 > MAX_ROWS:
            errors.append(f"File exceeds {MAX_ROWS} row limit; truncated at row {MAX_ROWS}")
            break
        raw_rows.append((i, row))

    if not raw_rows:
        return BOMImportPreviewResponse(
            new_rows=[], conflicts=[], errors=["CSV has no data rows"],
            column_mappings=column_mappings,
        )

    # Parse all rows
    all_skus: set[str] = set()
    parsed: list[dict] = []
    for line_num, row in raw_rows:
        parent_sku = _get_field(row, col_map, "parent_sku") or ""
        child_sku = _get_field(row, col_map, "child_sku") or ""
        qty_str = _get_field(row, col_map, "quantity") or ""
        ref_des = _get_field(row, col_map, "ref_designator")
        line_des = _get_field(row, col_map, "line_designator")
        uom = _get_field(row, col_map, "unit_of_measure")
        comp_type = _get_field(row, col_map, "component_type")
        notes = _get_field(row, col_map, "notes")

        row_errors: list[str] = []
        if not parent_sku or not child_sku:
            row_errors.append("parent_sku and child_sku are required")
        qty: Decimal | None = None
        try:
            qty = Decimal(qty_str)
            if qty <= 0:
                row_errors.append("quantity must be > 0")
                qty = None
        except (InvalidOperation, ValueError):
            row_errors.append(f"invalid quantity '{qty_str}'")

        if row_errors:
            errors.append(f"Row {line_num}: {'; '.join(row_errors)}")
            continue

        all_skus.add(parent_sku)
        all_skus.add(child_sku)
        parsed.append({
            "line": line_num,
            "parent_sku": parent_sku,
            "child_sku": child_sku,
            "quantity": qty,
            "ref_designator": ref_des,
            "line_designator": line_des,
            "unit_of_measure": uom,
            "component_type": comp_type,
            "notes": notes,
        })

    if not parsed:
        return BOMImportPreviewResponse(
            new_rows=[], conflicts=[], errors=errors,
            column_mappings=column_mappings,
        )

    # Batch SKU lookup
    products = db.query(Product).filter(Product.sku.in_(list(all_skus))).all()
    sku_map: dict[str, Product] = {p.sku: p for p in products}

    unknown = all_skus - set(sku_map.keys())
    for sku in sorted(unknown):
        errors.append(f"Unknown SKU: '{sku}'")

    valid_parsed = [
        r for r in parsed
        if r["parent_sku"] in sku_map and r["child_sku"] in sku_map
    ]

    if not valid_parsed:
        return BOMImportPreviewResponse(
            new_rows=[], conflicts=[], errors=errors,
            column_mappings=column_mappings,
        )

    # Load existing BOM items for all parent IDs
    parent_ids = {sku_map[r["parent_sku"]].id for r in valid_parsed}
    existing_items = (
        db.query(ProductBOMItem)
        .filter(ProductBOMItem.parent_product_id.in_(list(parent_ids)))
        .all()
    )
    existing_index: dict[tuple[int, int], ProductBOMItem] = {
        (item.parent_product_id, item.child_product_id): item
        for item in existing_items
    }

    for r in valid_parsed:
        parent = sku_map[r["parent_sku"]]
        child = sku_map[r["child_sku"]]
        key = (parent.id, child.id)

        if parent.id == child.id:
            errors.append(f"Row {r['line']}: {r['parent_sku']} cannot reference itself in BOM")
            continue

        row_obj = BOMImportRow(
            parent_sku=r["parent_sku"],
            child_sku=r["child_sku"],
            quantity=r["quantity"],
            ref_designator=r["ref_designator"],
            line_designator=r["line_designator"],
            unit_of_measure=r["unit_of_measure"],
            component_type=r["component_type"],
            notes=r["notes"],
            row_number=r["line"],
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
                    existing_line_designator=existing.line_designator,
                    new_line_designator=r["line_designator"],
                    existing_unit_of_measure=existing.unit_of_measure,
                    new_unit_of_measure=r["unit_of_measure"],
                    existing_component_type=existing.component_type,
                    new_component_type=r["component_type"],
                    existing_notes=existing.notes,
                    new_notes=r["notes"],
                )
            )
        else:
            new_rows.append(row_obj)

    return BOMImportPreviewResponse(
        new_rows=new_rows, conflicts=conflicts, errors=errors,
        column_mappings=column_mappings,
    )


# ---------------------------------------------------------------------------
# Apply import (Step 3)
# ---------------------------------------------------------------------------

def apply_bom_import(request: BOMImportApplyRequest, db: Session) -> BOMImportApplyResponse:
    created = updated = skipped = 0

    all_skus: set[str] = set()
    for row in request.rows:
        all_skus.add(row.parent_sku)
        all_skus.add(row.child_sku)

    products = db.query(Product).filter(Product.sku.in_(list(all_skus))).all()
    sku_map: dict[str, Product] = {p.sku: p for p in products}

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
            if (row.parent_sku, row.child_sku) in upsert_set:
                existing.quantity = row.quantity
                existing.reference_designator = row.ref_designator
                existing.line_designator = row.line_designator
                if row.unit_of_measure:
                    existing.unit_of_measure = row.unit_of_measure
                existing.component_type = row.component_type
                existing.notes = row.notes
                updated += 1
            else:
                skipped += 1
        else:
            item = ProductBOMItem(
                parent_product_id=parent.id,
                child_product_id=child.id,
                quantity=row.quantity,
                reference_designator=row.ref_designator,
                line_designator=row.line_designator,
                unit_of_measure=row.unit_of_measure or "EA",
                component_type=row.component_type,
                notes=row.notes,
            )
            db.add(item)
            created += 1

    db.commit()
    logger.info("BOM import applied: created=%d updated=%d skipped=%d", created, updated, skipped)
    return BOMImportApplyResponse(created=created, updated=updated, skipped=skipped)


# ---------------------------------------------------------------------------
# Template generation
# ---------------------------------------------------------------------------

def generate_template(template_type: str) -> str:
    if template_type == "mechanical":
        lines = [
            "parent_sku,child_sku,quantity,unit_of_measure,find_number,component_type,notes",
            "ASM-BRACKET-100,BOLT-M6X20,8,EA,3,material,M6x20 hex bolt",
            "ASM-BRACKET-100,PLATE-AL-6061,1,EA,1,material,6061-T6 aluminum plate",
            "ASM-BRACKET-100,WASHER-M6,8,EA,4,material,M6 flat washer",
        ]
    else:
        # Default: PCBA
        lines = [
            "parent_sku,child_sku,quantity,unit_of_measure,reference_designator,component_type,notes",
            "ASM-PCB-001,RES-10K-0402,4,EA,R1 R2 R3 R4,electronic,10K 0402 resistor",
            "ASM-PCB-001,CAP-100NF-0402,2,EA,C1 C2,electronic,100nF 0402 MLCC",
            "ASM-PCB-001,IC-MCU-STM32,1,EA,U1,electronic,STM32F4 microcontroller",
        ]
    return "\n".join(lines) + "\n"
