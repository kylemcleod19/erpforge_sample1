# BOM & Product Discovery — Interview Answers

**Date:** 2026-03-09
**Template:** `erp_bom_discovery_questions.md`
**Purpose:** Capture requirements for improving the BOM and product implementation in erpforge_sample1.

---

## Section 1 — Product Catalog Structure

| # | Question | Answer |
|---|----------|--------|
| 2 | Are products grouped into families or categories? | **Yes — families/categories** (e.g., products belong to named groupings) |
| 6 | Are products typically custom per customer order or standard SKUs? | **Standard SKUs only** — customers order from the catalog |
| 8 | How are product identifiers defined? | **SKU + revision** — part number with a separate numeric revision field |
| 73 | Do products move through lifecycle stages? | **Yes — prototype / production / end-of-life** — status affects planning |

---

## Section 2 — BOM Structure

| # | Question | Answer |
|---|----------|--------|
| 13 | Are assemblies reused across multiple products? | **Yes — heavily shared** — reuse is a core design principle |
| 11/12 | What BOM depth is typical? | **Varies by product** — some flat, some deeply nested |
| 14 | Can an assembly exist independently as a sellable item? | **Rarely** — sub-assemblies are mostly internal work products |
| 19 | Should BOM represent design structure, manufacturing structure, or both? | **Engineering structure only** — manufacturing sequences live in routings |

---

## Section 3 — Component Management

| # | Question | Answer |
|---|----------|--------|
| 21 | What types of components exist? | **Mechanical parts, Electronic/PCB, Raw materials, Consumables** |
| 22 | Are components always purchased, always manufactured, or both? | **Mix — make/buy per item** — each component has a make-or-buy designation |
| 25 | Can components have substitute parts? | **Yes — approved alternates** — list of approved substitute parts per component |
| 30 | Are component lifecycle states tracked? | **Active / obsolete only** — simple flag |

---

## Section 4 — PCB / Electronics

| # | Question | Answer |
|---|----------|--------|
| 31 | Are electronic components tracked by reference designator? | **Yes — reference designators required** (R1, C4, U7, etc.) |

---

## Section 5 — Revision and Change Management

| # | Question | Answer |
|---|----------|--------|
| 38 | Are revisions numeric, alphabetic, or date-based? | **Numeric** (1, 2, 3…) |
| 40/41 | Are changes tracked through formal change orders? | **Lightweight approval** — changes need a reviewer sign-off, no formal ECO workflow |
| 43 | Should previous BOM revisions remain accessible? | **Yes — full history** — all past revisions retained; work orders reference the revision used |

---

## Section 6 — Traceability

| # | Question | Answer |
|---|----------|--------|
| 45–47 | Which items require lot/serial tracking? | **Depends on SKU** — traceability type (none, serial, lot) configured per SKU. Some include supplier info in trace. |
| 48 | Is traceability required for regulatory reasons? | **Customer contract requirement** — tied to SKU; not a blanket regulatory mandate |

---

## Section 7 — Inventory and Consumables

| # | Question | Answer |
|---|----------|--------|
| 52 | Should consumables appear on the BOM? | **Yes — on BOM with estimated quantity** |

---

## Section 8 — Scrap and Overage

| # | Question | Answer |
|---|----------|--------|
| 56 | Should scrap factors be applied to components? | **Unsure / TBD** — not a current requirement |

---

## Section 9 — Configuration and Variants

| # | Question | Answer |
|---|----------|--------|
| 61 | Can products be configured with selectable options? | **Unsure / future** — not needed now |
| 64 | Are variant products assigned separate SKUs? | **Mix** — some variants are separate SKUs, others use options on a base product |

---

## Section 10 — Manufacturing Context

| # | Question | Answer |
|---|----------|--------|
| 67 | Are products built in a single facility or multiple? | **Single site** |
| 70/71 | Are packaging materials or tools included in BOM? | **Neither** — managed outside the BOM |

---

## Section 11 — Product Lifecycle

| # | Question | Answer |
|---|----------|--------|
| 75 | Should the system prevent use of obsolete components? | **Warning only** — user is warned but can override |
| 76 | Should historical production reference the BOM revision used at the time? | **Yes — snapshot the BOM revision** on each work order |

---

## Section 12 — Documentation and Metadata

| # | Question | Answer |
|---|----------|--------|
| 77 | Are engineering drawings linked to BOM items? | **Yes — per product level** (not per individual BOM line) |
| 78 | Are compliance documents required? | **Yes — for some products and components** (e.g., RoHS, certifications) — not universal |

---

## Key Themes from Discovery

1. **BOM versioning is critical** — full history, work order snapshots, lightweight approval
2. **Product structure needs metadata** — categories, lifecycle status, make/buy, traceability type per SKU, numeric revision
3. **BOM line items need enrichment** — reference designators (PCB), component type, alternate parts
4. **Alternate components** — approved alternates list per BOM line item
5. **Traceability is per-SKU** — not a global setting; some products need serial, some lot, some nothing
6. **Compliance is selective** — some products/components have compliance docs, not all
7. **Configurability is deferred** — not a current requirement
