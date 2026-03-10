# Plan: BOM & Product Implementation Improvements

## Context

Discovery interviews revealed the following gaps in the current BOM and product implementation:
- No BOM versioning or revision history
- Product records lack lifecycle status, category, make/buy, revision, and traceability type
- BOM line items lack reference designators (PCB requirement), component type, and alternate parts
- Work orders do not snapshot which BOM revision was active when created
- No compliance document tracking per product/component
- No warning when obsolete components are used

This plan adds these capabilities in four prioritized phases, building on existing conventions.

---

## Phase 1 — Product Record Enrichment

**New columns on `products` table:**

| Column | Type | Default |
|--------|------|---------|
| `category` | VARCHAR(100) | null |
| `revision` | INTEGER | 1 |
| `lifecycle_status` | VARCHAR(30) | `production` |
| `make_buy` | VARCHAR(10) | `buy` |
| `traceability_type` | VARCHAR(20) | `none` |
| `compliance_required` | BOOLEAN | false |

**Files changed:**
- `backend/app/models/product.py` — add 6 columns
- `backend/app/schemas/product.py` — extend ProductCreate/Update/Out
- `backend/alembic/versions/0002_product_enrichment.py` — migration
- `frontend/src/pages/Products.tsx` — add fields to create/edit drawer
- `frontend/src/pages/ProductDetail.tsx` — display new fields
- `frontend/src/api/products.ts` — extend TypeScript interface

**Obsolete component warning:** `POST /products/{id}/bom` checks child `lifecycle_status`; returns `warnings` array if `end_of_life`. Frontend shows Ant Design Alert.

---

## Phase 2 — BOM Revisions + Work Order Snapshot

**New table: `bom_revisions`**
```
id, product_id (FK), revision_number, status (draft|pending_approval|approved|superseded),
notes, created_at, approved_by, approved_at
UNIQUE(product_id, revision_number)
```

**Columns added:**
- `product_bom_items.bom_revision_id` → FK to `bom_revisions`
- `work_orders.bom_revision_id` → FK to `bom_revisions`

**New endpoints:**
- `GET /products/{id}/bom-revisions`
- `POST /products/{id}/bom-revisions`
- `PATCH /products/{id}/bom-revisions/{rev_id}/approve`
- `GET /products/{id}/bom-revisions/{rev_id}/bom`

**Service changes:**
- `order_service.py` — snapshot active BOM revision when creating work order
- `bom_service.py` — `compute_cost_rollup` accepts optional `revision_id`

**Files changed:**
- `backend/app/models/product.py`, `manufacturing.py`
- `backend/app/schemas/product.py`
- `backend/app/routers/products.py`
- `backend/app/services/order_service.py`, `bom_service.py`
- `backend/alembic/versions/0003_bom_revisions.py`
- `frontend/src/pages/ProductDetail.tsx` — BOM Revisions panel
- `frontend/src/pages/WorkOrders.tsx` — show BOM revision reference

---

## Phase 3 — BOM Line Enrichment + Alternate Components

**Columns added to `product_bom_items`:**

| Column | Type | Notes |
|--------|------|-------|
| `reference_designator` | VARCHAR(50) | PCB ref des (R1, C4, U7) |
| `component_type` | VARCHAR(30) | material, subassembly, electronic, consumable, service |
| `notes` | TEXT | Line-level notes |

**New table: `bom_item_alternates`**
```
id, bom_item_id (FK), alternate_product_id (FK), priority, notes
```

**New endpoints:**
- `GET /products/{id}/bom/{bom_item_id}/alternates`
- `POST /products/{id}/bom/{bom_item_id}/alternates`
- `DELETE /products/{id}/bom/{bom_item_id}/alternates/{alt_id}`

**Files changed:**
- `backend/app/models/product.py`
- `backend/app/schemas/product.py`
- `backend/app/routers/products.py`
- `backend/alembic/versions/0004_bom_line_enrichment.py`
- `frontend/src/pages/ProductDetail.tsx` — ref des + component type columns, expandable alternates row

---

## Phase 4 — Compliance Document Tracking

**New table: `product_compliance`**
```
id, product_id (FK), scope (product|component), cert_type (RoHS/CE/UL/etc.),
cert_number, issued_date, expiry_date, document_url, notes, created_at
```

**New endpoints:**
- `GET /products/{id}/compliance`
- `POST /products/{id}/compliance`
- `DELETE /products/{id}/compliance/{cert_id}`

**Files changed:**
- `backend/app/models/product.py`
- `backend/app/schemas/product.py`
- `backend/app/routers/products.py`
- `backend/alembic/versions/0005_product_compliance.py`
- `frontend/src/pages/ProductDetail.tsx` — Compliance section

---

## Verification (after each phase)

1. `make reset && make migrate`
2. `POST /products` — confirm new fields accepted and returned
3. `http://localhost:3000` — confirm UI shows new fields
4. Phase 2: create + approve BOM revision; convert quote to order; verify `work_orders.bom_revision_id` is set
5. Phase 3: add BOM item with ref des; add alternate; verify via GET
6. `http://localhost:8000/docs` — all new endpoints visible in Swagger

---

## Discovery Q&A Source

`C:\src\erpforge_sample1\.claude\interview_templates\bom_product_discovery_answers.md`
