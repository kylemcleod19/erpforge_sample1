from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.invoice import Invoice, InvoiceLineItem
from app.models.order import Order
from app.models.shipping import Shipment


def _generate_invoice_number(db: Session) -> str:
    now = datetime.now(timezone.utc)
    prefix = f"INV-{now.strftime('%Y%m')}-"
    count = (
        db.query(func.count(Invoice.id))
        .filter(Invoice.invoice_number.like(f"{prefix}%"))
        .scalar()
        or 0
    )
    return f"{prefix}{count + 1:04d}"


def create_invoice_for_shipment(shipment: Shipment, db: Session) -> Invoice:
    order = db.get(Order, shipment.order_id)
    if not order:
        raise ValueError(f"Order {shipment.order_id} not found")

    invoice_number = _generate_invoice_number(db)

    subtotal = sum(li.quantity * li.unit_price for li in order.line_items)
    tax_amount = subtotal * 0  # 0% tax; configurable
    total_amount = subtotal + tax_amount

    invoice = Invoice(
        order_id=order.id,
        shipment_id=shipment.id,
        invoice_number=invoice_number,
        status="draft",
        subtotal=subtotal,
        tax_amount=tax_amount,
        total_amount=total_amount,
    )
    db.add(invoice)
    db.flush()

    for li in order.line_items:
        product_name = li.product.name if li.product else str(li.product_id)
        line_subtotal = li.quantity * li.unit_price
        inv_li = InvoiceLineItem(
            invoice_id=invoice.id,
            product_id=li.product_id,
            description=product_name,
            quantity=li.quantity,
            unit_price=li.unit_price,
            subtotal=line_subtotal,
        )
        db.add(inv_li)

    # Update order status to shipped
    order.status = "shipped"

    db.flush()
    return invoice
