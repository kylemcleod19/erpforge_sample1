# Design: SKU and Product Name on Order Line Items

**Date:** 2026-03-13
**Status:** Implemented

## Problem Statement

Order line items were missing SKU and product name in API responses, making it impossible for users to identify products on an order without cross-referencing elsewhere.

## Root Cause

This was a bug, not a missing feature. The schema (`OrderLineItemOut`), enrichment helper (`_enrich_line_item`), and frontend columns were all already in place. The `list_orders` and `get_order` endpoints returned raw SQLAlchemy ORM objects directly, so Pydantic serialized `product_name`/`product_sku` as `null` because those fields are on the related `Product` model, not direct columns on `OrderLineItem`.

## Fix

Added `_enrich_order()` helper in `backend/app/routers/orders.py` that wraps the ORM `Order` into an explicit `OrderOut` with each line item passed through `_enrich_line_item()`. All three endpoints (`GET /orders`, `GET /orders/{id}`, `PATCH /orders/{id}/status`) now return `_enrich_order(order)`.

## Data Model Changes

None. No migration required.

## API Changes

No schema changes. `product_name` and `product_sku` in `OrderLineItemOut` now return populated values instead of null.

## Frontend Changes

None. `OrderDetail.tsx` already had "SKU" and "Product" columns bound to the correct fields.

## Acceptance Criteria

- [x] `GET /orders/{id}` returns non-null `product_sku` and `product_name` on each line item
- [x] `GET /orders` list also returns enriched line items
- [x] `OrderDetail` page shows SKU and product name in the line items table
- [x] No regression on order status update, work orders, or reservation sections
