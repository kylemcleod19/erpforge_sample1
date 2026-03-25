import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import assistant, auth, invoices, manufacturing, onboarding, orders, products, purchasing, quotes, shipping, inventory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ERPForge Sample ERP",
    version="1.0.0",
    description="Manufacturing ERP reference implementation",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(onboarding.router)
app.include_router(assistant.router)
app.include_router(products.router)
app.include_router(quotes.router)
app.include_router(orders.router)
app.include_router(inventory.router)
app.include_router(purchasing.router)
app.include_router(manufacturing.router)
app.include_router(shipping.router)
app.include_router(invoices.router)


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "service": "erpforge-backend"}
