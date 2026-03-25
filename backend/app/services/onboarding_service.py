from sqlalchemy.orm import Session

from app.models.inventory import InventoryBalance
from app.models.manufacturing import WorkStation
from app.models.onboarding import OnboardingProgress
from app.models.order import Order
from app.models.product import Product, ProductBOMItem
from app.models.quote import Quote
from app.models.shipping import Shipment
from app.models.user import User


MILESTONES = {
    "first_product": {
        "label": "Create your first product",
        "description": "Add a finished good or assembly to the product catalog",
        "roles": ["admin", "engineer"],
        "copilot_prompt": "Help me create my first product",
    },
    "first_component": {
        "label": "Add a component",
        "description": "Create a raw material or component for use in BOMs",
        "roles": ["admin", "engineer"],
        "copilot_prompt": "Help me create a component for my BOM",
    },
    "first_bom": {
        "label": "Build a bill of materials",
        "description": "Add BOM items to a product",
        "roles": ["admin", "engineer"],
        "copilot_prompt": "Help me build a bill of materials for a product",
    },
    "first_station": {
        "label": "Set up a work station",
        "description": "Define a manufacturing station",
        "roles": ["admin", "engineer"],
        "copilot_prompt": "Help me set up my first work station",
    },
    "first_quote": {
        "label": "Create your first quote",
        "description": "Start a quote for a customer",
        "roles": ["admin", "sales"],
        "copilot_prompt": "Help me create a quote for a customer",
    },
    "first_quote_won": {
        "label": "Win a quote",
        "description": "Mark a quote as won by the customer",
        "roles": ["admin", "sales"],
        "copilot_prompt": "Help me move a quote through the approval process",
    },
    "first_order": {
        "label": "Convert a quote to an order",
        "description": "Convert a won quote to generate an order with all downstream artifacts",
        "roles": ["admin", "sales"],
        "copilot_prompt": "Help me convert a won quote into an order",
    },
    "first_shipment": {
        "label": "Ship an order",
        "description": "Create a shipment to auto-generate an invoice",
        "roles": ["admin", "sales"],
        "copilot_prompt": "Help me create a shipment for an order",
    },
}


def _check_milestone(key: str, db: Session) -> bool:
    checks = {
        "first_product": lambda: db.query(Product).filter(
            Product.item_type.in_(["finished_good", "assembly"])
        ).count() > 0,
        "first_component": lambda: db.query(Product).filter(
            Product.item_type.in_(["component", "raw_material"])
        ).count() > 0,
        "first_bom": lambda: db.query(ProductBOMItem).count() > 0,
        "first_station": lambda: db.query(WorkStation).count() > 0,
        "first_quote": lambda: db.query(Quote).count() > 0,
        "first_quote_won": lambda: db.query(Quote).filter(Quote.status == "won").count() > 0,
        "first_order": lambda: db.query(Order).count() > 0,
        "first_shipment": lambda: db.query(Shipment).count() > 0,
    }
    check = checks.get(key)
    return check() if check else False


def get_or_create_progress(user: User, db: Session) -> OnboardingProgress:
    progress = db.query(OnboardingProgress).filter(OnboardingProgress.user_id == user.id).first()
    if not progress:
        progress = OnboardingProgress(user_id=user.id, milestones_completed=[])
        db.add(progress)
        db.commit()
        db.refresh(progress)
    return progress


def refresh_milestones(user: User, db: Session) -> OnboardingProgress:
    progress = get_or_create_progress(user, db)
    completed = []
    for key, info in MILESTONES.items():
        if user.role in info["roles"] and _check_milestone(key, db):
            completed.append(key)
    progress.milestones_completed = completed
    db.commit()
    db.refresh(progress)
    return progress


def get_progress_response(user: User, db: Session) -> dict:
    progress = refresh_milestones(user, db)
    completed_set = set(progress.milestones_completed or [])
    milestones = []
    for key, info in MILESTONES.items():
        if user.role in info["roles"]:
            milestones.append({
                "key": key,
                "label": info["label"],
                "description": info["description"],
                "completed": key in completed_set,
                "copilot_prompt": info["copilot_prompt"],
            })
    total = len(milestones)
    done = sum(1 for m in milestones if m["completed"])
    return {
        "milestones": milestones,
        "total": total,
        "completed_count": done,
        "dismissed": progress.dismissed,
    }
