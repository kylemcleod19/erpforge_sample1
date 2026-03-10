from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.product import Product, ProductBOMItem
from app.schemas.product import CostNode


def _query_bom_items(
    product_id: int, db: Session, revision_id: int | None
) -> list[ProductBOMItem]:
    """Fetch BOM items for a product, optionally filtered by revision."""
    q = db.query(ProductBOMItem).filter(ProductBOMItem.parent_product_id == product_id)
    if revision_id is not None:
        q = q.filter(ProductBOMItem.bom_revision_id == revision_id)
    return q.all()


def get_bom_tree(
    product_id: int,
    db: Session,
    visited: set[int] | None = None,
    revision_id: int | None = None,
) -> dict:
    """
    Recursively build a BOM tree for a product.
    Returns a nested dict structure.
    Guards against circular references via `visited`.
    Pass revision_id to scope to a specific BOM revision.
    """
    if visited is None:
        visited = set()

    if product_id in visited:
        raise ValueError(f"Circular BOM reference detected at product_id={product_id}")

    visited = visited | {product_id}

    product = db.get(Product, product_id)
    if not product:
        return {}

    bom_items = _query_bom_items(product_id, db, revision_id)

    children = []
    for item in bom_items:
        child_tree = get_bom_tree(item.child_product_id, db, visited, revision_id)
        child_tree["bom_quantity"] = float(item.quantity)
        child_tree["bom_uom"] = item.unit_of_measure
        children.append(child_tree)

    return {
        "product_id": product.id,
        "sku": product.sku,
        "name": product.name,
        "unit_cost": float(product.unit_cost),
        "unit_price": float(product.unit_price),
        "children": children,
    }


def compute_cost_rollup(
    product_id: int,
    db: Session,
    visited: set[int] | None = None,
    revision_id: int | None = None,
) -> CostNode:
    """
    Recursively compute cost rollup.
    rolled_up_cost = own unit_cost + sum(child_qty * child_rolled_up_cost)
    Pass revision_id to scope cost computation to a specific BOM revision.
    """
    if visited is None:
        visited = set()

    if product_id in visited:
        raise ValueError(f"Circular BOM reference at product_id={product_id}")

    visited = visited | {product_id}

    product = db.get(Product, product_id)
    if not product:
        raise ValueError(f"Product {product_id} not found")

    bom_items = _query_bom_items(product_id, db, revision_id)

    children: list[CostNode] = []
    children_cost = Decimal("0")

    for item in bom_items:
        child_node = compute_cost_rollup(item.child_product_id, db, visited, revision_id)
        children.append(child_node)
        children_cost += item.quantity * child_node.rolled_up_cost

    rolled_up_cost = product.unit_cost + children_cost

    return CostNode(
        product_id=product.id,
        sku=product.sku,
        name=product.name,
        unit_cost=product.unit_cost,
        rolled_up_cost=rolled_up_cost,
        children=children,
    )
