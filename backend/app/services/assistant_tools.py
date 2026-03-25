import logging

from sqlalchemy.orm import Session

from app.models.inventory import InventoryBalance
from app.models.manufacturing import WorkStation
from app.models.order import Order
from app.models.product import Product, ProductBOMItem
from app.models.quote import Quote, QuoteLineItem
from app.models.shipping import Shipment
from app.models.user import User
from app.services.invoice_service import create_invoice_for_shipment
from app.services.order_service import convert_quote_to_order

logger = logging.getLogger(__name__)

VALID_QUOTE_TRANSITIONS = {
    "draft": ["review"],
    "review": ["approved", "draft"],
    "approved": ["sent"],
    "sent": ["won", "lost"],
}

# Tool definitions for Claude API
TOOL_DEFINITIONS = [
    {
        "name": "list_products",
        "description": "List products, optionally filtered by item_type. Returns up to 20 results.",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_type": {
                    "type": "string",
                    "enum": ["finished_good", "assembly", "component", "raw_material"],
                    "description": "Filter by item type",
                },
            },
        },
    },
    {
        "name": "create_product",
        "description": "Create a new product or component in the catalog.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sku": {"type": "string", "description": "Unique product SKU"},
                "name": {"type": "string", "description": "Product name"},
                "item_type": {
                    "type": "string",
                    "enum": ["finished_good", "assembly", "component", "raw_material"],
                },
                "unit_cost": {"type": "number", "description": "Cost per unit"},
                "unit_price": {"type": "number", "description": "Selling price per unit"},
                "unit_of_measure": {"type": "string", "description": "Unit of measure, e.g. EA, KG, M"},
                "category": {"type": "string"},
                "description": {"type": "string"},
            },
            "required": ["sku", "name", "item_type"],
        },
    },
    {
        "name": "add_bom_item",
        "description": "Add a component to a product's bill of materials.",
        "input_schema": {
            "type": "object",
            "properties": {
                "parent_product_id": {"type": "integer", "description": "ID of the parent product"},
                "child_product_id": {"type": "integer", "description": "ID of the component to add"},
                "quantity": {"type": "number", "description": "Quantity needed per parent unit"},
                "unit_of_measure": {"type": "string"},
                "reference_designator": {"type": "string"},
                "notes": {"type": "string"},
            },
            "required": ["parent_product_id", "child_product_id", "quantity"],
        },
    },
    {
        "name": "create_quote",
        "description": "Create a new quote for a customer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_name": {"type": "string"},
                "customer_email": {"type": "string"},
                "notes": {"type": "string"},
            },
            "required": ["customer_name"],
        },
    },
    {
        "name": "add_quote_line_item",
        "description": "Add a line item to an existing quote.",
        "input_schema": {
            "type": "object",
            "properties": {
                "quote_id": {"type": "integer"},
                "product_id": {"type": "integer"},
                "quantity": {"type": "number"},
                "unit_price": {"type": "number"},
            },
            "required": ["quote_id", "product_id", "quantity", "unit_price"],
        },
    },
    {
        "name": "transition_quote_status",
        "description": "Change a quote's status. Valid transitions: draft->review, review->approved, approved->sent, sent->won/lost.",
        "input_schema": {
            "type": "object",
            "properties": {
                "quote_id": {"type": "integer"},
                "new_status": {"type": "string", "enum": ["review", "approved", "sent", "won", "lost"]},
            },
            "required": ["quote_id", "new_status"],
        },
    },
    {
        "name": "convert_quote_to_order",
        "description": "Convert a won quote into an order. This creates the order, inventory reservations, purchase requests for shortages, and work orders for products with routings.",
        "input_schema": {
            "type": "object",
            "properties": {
                "quote_id": {"type": "integer"},
            },
            "required": ["quote_id"],
        },
    },
    {
        "name": "create_station",
        "description": "Create a manufacturing work station.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "sequence": {"type": "integer"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "adjust_inventory",
        "description": "Set the on-hand inventory balance for a product.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "integer"},
                "quantity_on_hand": {"type": "number"},
            },
            "required": ["product_id", "quantity_on_hand"],
        },
    },
    {
        "name": "create_shipment",
        "description": "Create a shipment for an order. This auto-generates an invoice.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "integer"},
                "carrier": {"type": "string"},
                "tracking_number": {"type": "string"},
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "get_app_state_summary",
        "description": "Get a summary of current data in the system (counts of products, orders, quotes, etc.).",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "navigate_user",
        "description": "Suggest the user navigate to a specific page in the application.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The URL path, e.g. /products, /quotes/5"},
                "reason": {"type": "string", "description": "Why the user should navigate there"},
            },
            "required": ["path"],
        },
    },
]


def execute_tool(tool_name: str, tool_input: dict, db: Session, user: User) -> str:
    """Execute a copilot tool and return a text result for Claude."""
    try:
        match tool_name:
            case "list_products":
                q = db.query(Product)
                if tool_input.get("item_type"):
                    q = q.filter(Product.item_type == tool_input["item_type"])
                products = q.limit(20).all()
                if not products:
                    return "No products found."
                lines = [f"- {p.sku}: {p.name} (ID={p.id}, type={p.item_type}, price=${float(p.unit_price):.2f})" for p in products]
                return f"Found {len(products)} product(s):\n" + "\n".join(lines)

            case "create_product":
                existing = db.query(Product).filter(Product.sku == tool_input["sku"]).first()
                if existing:
                    return f"Error: Product with SKU '{tool_input['sku']}' already exists (ID={existing.id})."
                product = Product(
                    sku=tool_input["sku"],
                    name=tool_input["name"],
                    item_type=tool_input.get("item_type", "finished_good"),
                    unit_cost=tool_input.get("unit_cost", 0),
                    unit_price=tool_input.get("unit_price", 0),
                    unit_of_measure=tool_input.get("unit_of_measure", "EA"),
                    category=tool_input.get("category"),
                    description=tool_input.get("description"),
                )
                db.add(product)
                db.commit()
                db.refresh(product)
                return f"Created product '{product.name}' (SKU: {product.sku}, ID: {product.id}, type: {product.item_type})."

            case "add_bom_item":
                parent = db.get(Product, tool_input["parent_product_id"])
                if not parent:
                    return f"Error: Parent product ID {tool_input['parent_product_id']} not found."
                child = db.get(Product, tool_input["child_product_id"])
                if not child:
                    return f"Error: Child product ID {tool_input['child_product_id']} not found."
                bom_item = ProductBOMItem(
                    parent_product_id=parent.id,
                    child_product_id=child.id,
                    quantity=tool_input["quantity"],
                    unit_of_measure=tool_input.get("unit_of_measure", "EA"),
                    reference_designator=tool_input.get("reference_designator"),
                    notes=tool_input.get("notes"),
                )
                db.add(bom_item)
                db.commit()
                return f"Added {child.sku} (qty: {tool_input['quantity']}) to BOM of {parent.sku}."

            case "create_quote":
                quote = Quote(
                    customer_name=tool_input["customer_name"],
                    customer_email=tool_input.get("customer_email"),
                    notes=tool_input.get("notes"),
                    status="draft",
                )
                db.add(quote)
                db.commit()
                db.refresh(quote)
                return f"Created quote #{quote.id} for customer '{quote.customer_name}' (status: draft)."

            case "add_quote_line_item":
                quote = db.get(Quote, tool_input["quote_id"])
                if not quote:
                    return f"Error: Quote #{tool_input['quote_id']} not found."
                if quote.status in ("won", "lost"):
                    return f"Error: Cannot add items to a {quote.status} quote."
                product = db.get(Product, tool_input["product_id"])
                if not product:
                    return f"Error: Product ID {tool_input['product_id']} not found."
                subtotal = tool_input["quantity"] * tool_input["unit_price"]
                li = QuoteLineItem(
                    quote_id=quote.id,
                    product_id=product.id,
                    quantity=tool_input["quantity"],
                    unit_price=tool_input["unit_price"],
                    subtotal=subtotal,
                )
                db.add(li)
                db.commit()
                return f"Added {product.name} (qty: {tool_input['quantity']}, unit price: ${tool_input['unit_price']:.2f}, subtotal: ${subtotal:.2f}) to quote #{quote.id}."

            case "transition_quote_status":
                quote = db.get(Quote, tool_input["quote_id"])
                if not quote:
                    return f"Error: Quote #{tool_input['quote_id']} not found."
                allowed = VALID_QUOTE_TRANSITIONS.get(quote.status, [])
                if tool_input["new_status"] not in allowed:
                    return f"Error: Cannot transition from '{quote.status}' to '{tool_input['new_status']}'. Allowed: {allowed}."
                quote.status = tool_input["new_status"]
                db.commit()
                return f"Quote #{quote.id} status changed to '{quote.status}'."

            case "convert_quote_to_order":
                order = convert_quote_to_order(tool_input["quote_id"], db)
                li_count = len(order.line_items)
                return f"Converted quote #{tool_input['quote_id']} to Order #{order.id} with {li_count} line item(s). Inventory reservations, purchase requests, and work orders have been created as needed."

            case "create_station":
                station = WorkStation(
                    name=tool_input["name"],
                    description=tool_input.get("description"),
                    sequence=tool_input.get("sequence", 0),
                )
                db.add(station)
                db.commit()
                db.refresh(station)
                return f"Created work station '{station.name}' (ID: {station.id}, sequence: {station.sequence})."

            case "adjust_inventory":
                product = db.get(Product, tool_input["product_id"])
                if not product:
                    return f"Error: Product ID {tool_input['product_id']} not found."
                balance = db.query(InventoryBalance).filter(
                    InventoryBalance.product_id == tool_input["product_id"]
                ).first()
                if balance:
                    balance.quantity_on_hand = tool_input["quantity_on_hand"]
                else:
                    balance = InventoryBalance(
                        product_id=tool_input["product_id"],
                        quantity_on_hand=tool_input["quantity_on_hand"],
                    )
                    db.add(balance)
                db.commit()
                return f"Inventory for {product.sku} set to {tool_input['quantity_on_hand']} {product.unit_of_measure}."

            case "create_shipment":
                order = db.get(Order, tool_input["order_id"])
                if not order:
                    return f"Error: Order #{tool_input['order_id']} not found."
                shipment = Shipment(
                    order_id=order.id,
                    carrier=tool_input.get("carrier"),
                    tracking_number=tool_input.get("tracking_number"),
                )
                db.add(shipment)
                db.flush()
                create_invoice_for_shipment(shipment, db)
                db.commit()
                db.refresh(shipment)
                return f"Created shipment #{shipment.id} for Order #{order.id}. Invoice has been auto-generated."

            case "get_app_state_summary":
                return _get_app_state(db)

            case "navigate_user":
                reason = tool_input.get("reason", "")
                return f"NAVIGATE:{tool_input['path']}|{reason}"

            case _:
                return f"Error: Unknown tool '{tool_name}'."

    except Exception as e:
        logger.exception("Tool execution error: %s", tool_name)
        db.rollback()
        return f"Error executing {tool_name}: {str(e)}"


def _get_app_state(db: Session) -> str:
    product_count = db.query(Product).count()
    fg_count = db.query(Product).filter(Product.item_type.in_(["finished_good", "assembly"])).count()
    comp_count = db.query(Product).filter(Product.item_type.in_(["component", "raw_material"])).count()
    bom_count = db.query(ProductBOMItem).count()
    quote_count = db.query(Quote).count()
    quote_won = db.query(Quote).filter(Quote.status == "won").count()
    order_count = db.query(Order).count()
    station_count = db.query(WorkStation).count()
    balance_count = db.query(InventoryBalance).count()
    shipment_count = db.query(Shipment).count()

    lines = [
        f"Products: {product_count} total ({fg_count} finished goods/assemblies, {comp_count} components/raw materials)",
        f"BOM items: {bom_count}",
        f"Quotes: {quote_count} (won: {quote_won})",
        f"Orders: {order_count}",
        f"Work Stations: {station_count}",
        f"Inventory balances tracked: {balance_count}",
        f"Shipments: {shipment_count}",
    ]

    if product_count == 0:
        lines.append("\nThe system is empty. The user should start by creating products or components.")
    elif bom_count == 0:
        lines.append("\nProducts exist but no BOMs have been created yet.")
    elif quote_count == 0:
        lines.append("\nProducts and BOMs exist. The next step is typically to create a quote.")

    return "\n".join(lines)


def get_app_state_for_prompt(db: Session) -> str:
    """Get app state summary formatted for the system prompt."""
    return _get_app_state(db)
