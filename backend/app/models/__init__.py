# Import all models so Alembic can discover them
from app.models.product import Product, ProductBOMItem, ProductSpec  # noqa: F401
from app.models.quote import Quote, QuoteLineItem  # noqa: F401
from app.models.order import Order, OrderLineItem  # noqa: F401
from app.models.inventory import InventoryBalance, InventoryReservation  # noqa: F401
from app.models.purchasing import PurchaseRequest  # noqa: F401
from app.models.manufacturing import WorkStation, ProductRouting, WorkOrder, WorkOrderLog  # noqa: F401
from app.models.shipping import Shipment  # noqa: F401
from app.models.invoice import Invoice, InvoiceLineItem  # noqa: F401
