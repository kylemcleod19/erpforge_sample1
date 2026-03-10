"""
order_service.py

Handles quote → order conversion including:
- Creating Order + OrderLineItems
- Traversing BOM to find all components
- Creating InventoryReservations for available stock
- Creating PurchaseRequests for shortages
- Creating WorkOrders for products with routings
"""
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.inventory import InventoryBalance, InventoryReservation
from app.models.manufacturing import ProductRouting, WorkOrder
from app.models.order import Order, OrderLineItem
from app.models.product import BOMRevision, Product, ProductBOMItem
from app.models.purchasing import PurchaseRequest
from app.models.quote import Quote


def _collect_bom_components(
    product_id: int,
    qty_multiplier: Decimal,
    db: Session,
    visited: set[int] | None = None,
) -> dict[int, Decimal]:
    """
    Recursively collect all leaf/intermediate components with total quantities needed.
    Returns: {product_id: total_quantity_needed}
    """
    if visited is None:
        visited = set()

    if product_id in visited:
        return {}

    visited = visited | {product_id}

    bom_items = (
        db.query(ProductBOMItem)
        .filter(ProductBOMItem.parent_product_id == product_id)
        .all()
    )

    components: dict[int, Decimal] = {}

    for item in bom_items:
        child_qty = item.quantity * qty_multiplier
        # Add this component itself
        components[item.child_product_id] = (
            components.get(item.child_product_id, Decimal("0")) + child_qty
        )
        # Recurse into child's BOM
        sub_components = _collect_bom_components(item.child_product_id, child_qty, db, visited)
        for pid, qty in sub_components.items():
            components[pid] = components.get(pid, Decimal("0")) + qty

    return components


def _collect_sub_assemblies_with_routing(
    product_id: int,
    db: Session,
    visited: set[int] | None = None,
) -> list[int]:
    """
    Recursively collect product IDs at all BOM levels that have a routing defined.
    Excludes the top-level product itself (handled separately).
    """
    if visited is None:
        visited = set()

    if product_id in visited:
        return []

    visited = visited | {product_id}

    result = []
    bom_items = (
        db.query(ProductBOMItem)
        .filter(ProductBOMItem.parent_product_id == product_id)
        .all()
    )

    for item in bom_items:
        child_id = item.child_product_id
        has_routing = (
            db.query(ProductRouting)
            .filter(ProductRouting.product_id == child_id)
            .first()
        ) is not None
        if has_routing:
            result.append(child_id)
        result.extend(_collect_sub_assemblies_with_routing(child_id, db, visited))

    return result


def _get_approved_bom_revision_id(product_id: int, db: Session) -> int | None:
    """Return the ID of the current approved BOM revision for a product, or None."""
    rev = (
        db.query(BOMRevision)
        .filter(
            BOMRevision.product_id == product_id,
            BOMRevision.status == "approved",
        )
        .order_by(BOMRevision.revision_number.desc())
        .first()
    )
    return rev.id if rev else None


def convert_quote_to_order(quote_id: int, db: Session) -> Order:
    quote = db.get(Quote, quote_id)
    if not quote:
        raise ValueError(f"Quote {quote_id} not found")
    if quote.status != "won":
        raise ValueError(f"Only won quotes can be converted. Current status: {quote.status}")

    # Check if already converted
    existing_order = db.query(Order).filter(Order.quote_id == quote_id).first()
    if existing_order:
        raise ValueError(f"Quote {quote_id} has already been converted to order {existing_order.id}")

    # 1. Create order
    order = Order(quote_id=quote_id, status="pending")
    db.add(order)
    db.flush()

    # 2. Create order line items
    for qli in quote.line_items:
        oli = OrderLineItem(
            order_id=order.id,
            product_id=qli.product_id,
            quantity=qli.quantity,
            unit_price=qli.unit_price,
        )
        db.add(oli)

    db.flush()

    # 3. For each order line item, process inventory and manufacturing
    for oli in order.line_items:
        product_id = oli.product_id
        order_qty = oli.quantity

        # --- Inventory: collect all BOM components ---
        components = _collect_bom_components(product_id, order_qty, db)

        for comp_id, needed_qty in components.items():
            balance = (
                db.query(InventoryBalance)
                .filter(InventoryBalance.product_id == comp_id)
                .first()
            )
            on_hand = balance.quantity_on_hand if balance else Decimal("0")

            can_reserve = min(on_hand, needed_qty)
            if can_reserve > 0:
                reservation = InventoryReservation(
                    order_id=order.id,
                    product_id=comp_id,
                    quantity_reserved=can_reserve,
                )
                db.add(reservation)
                # Reduce on-hand
                if balance:
                    balance.quantity_on_hand -= can_reserve

            shortage = needed_qty - can_reserve
            if shortage > 0:
                pr = PurchaseRequest(
                    order_id=order.id,
                    product_id=comp_id,
                    quantity_needed=shortage,
                    status="pending",
                )
                db.add(pr)

        # --- Manufacturing: create work order for top-level product ---
        top_routing = (
            db.query(ProductRouting)
            .filter(ProductRouting.product_id == product_id)
            .order_by(ProductRouting.sequence)
            .first()
        )
        if top_routing:
            wo = WorkOrder(
                order_id=order.id,
                product_id=product_id,
                quantity=order_qty,
                status="queued",
                current_station_sequence=top_routing.sequence,
                bom_revision_id=_get_approved_bom_revision_id(product_id, db),
            )
            db.add(wo)

        # Work orders for sub-assemblies with routing
        sub_assembly_ids = _collect_sub_assemblies_with_routing(product_id, db)
        for sub_id in set(sub_assembly_ids):
            sub_routing = (
                db.query(ProductRouting)
                .filter(ProductRouting.product_id == sub_id)
                .order_by(ProductRouting.sequence)
                .first()
            )
            if sub_routing:
                wo = WorkOrder(
                    order_id=order.id,
                    product_id=sub_id,
                    quantity=order_qty,
                    status="queued",
                    current_station_sequence=sub_routing.sequence,
                    bom_revision_id=_get_approved_bom_revision_id(sub_id, db),
                )
                db.add(wo)

    db.commit()
    db.refresh(order)
    return order
