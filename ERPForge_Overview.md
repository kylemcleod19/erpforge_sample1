# ERPForge — Platform Overview

ERPForge is a manufacturing ERP reference application built as a **FastAPI monolith + React frontend**, deployed via Docker Compose with PostgreSQL. It demonstrates realistic manufacturing ERP patterns across eight integrated domain modules.

---

## Architecture at a Glance

| Layer       | Technology                                  |
|-------------|---------------------------------------------|
| Backend     | Python 3.12, FastAPI 0.111, SQLAlchemy 2.0, Pydantic v2 |
| Frontend    | React 18, Vite, Ant Design v5, React Router v6 |
| Database    | PostgreSQL 15, Alembic migrations           |
| Auth        | JWT (bcrypt + HS256), role-based (admin, engineer, sales) |
| AI Copilot  | Claude API (Anthropic SDK) with tool use, SSE streaming |
| Deploy (local) | Docker Compose (backend, frontend, db)   |
| Deploy (prod)  | Railway (separate backend + frontend services, Railway-managed PostgreSQL) |

---

## Modules

### 1. Products & BOM Management

The core master-data module. Manages products classified by **item type** (`finished_good`, `assembly`, `component`, `raw_material`) with full lifecycle tracking (`prototype` → `production` → `end_of_life`).

**Capabilities:**
- Product CRUD with category, revision, traceability type, compliance flag
- **Multi-level Bill of Materials** — recursive parent/child relationships with quantity, unit of measure, reference designator, line designator, component type, and notes
- **BOM Revisions** — draft → pending_approval → approved → superseded; only one approved revision per product at a time
- **BOM Alternates** — prioritized alternate components per BOM line item
- **BOM CSV Import** — three-step flow: column auto-detection (40+ aliases) → mapping review → preview with conflict detection → apply
- **Downloadable CSV templates** for PCBA and Mechanical BOMs
- **Cost Rollup** — depth-first recursive calculation of rolled-up cost through the BOM tree
- **Specifications** — attach document URLs (datasheets, drawings)
- **Compliance Tracking** — certifications with scope, type, cert number, issued/expiry dates, document URL

### 2. Quotes

Sales quote lifecycle from creation through customer acceptance.

**Capabilities:**
- Quote CRUD with customer name, email, expiration, notes
- Line item management (product, quantity, unit price, lead time)
- **Status machine:** `draft` → `review` → `approved` → `sent` → `won` (or `lost` from any state)
- **Quote-to-Order conversion** — triggers the full downstream manufacturing and inventory workflow

### 3. Orders

Sales orders created from won quotes or manually.

**Capabilities:**
- Order CRUD with line items mirrored from quotes
- **Status tracking:** `pending` → `in_progress` → `shipped` → `invoiced` → `cancelled`
- Order detail view aggregates related reservations, purchase requests, work orders, shipments, and invoices

### 4. Inventory

Stock balance and reservation management.

**Capabilities:**
- **Inventory balances** — one balance per product (unique constraint), upsert capability
- **Inventory reservations** — auto-created during quote-to-order conversion for available stock
- Quantity tracking with decimal precision (Numeric 14,4) for fractional units

### 5. Purchasing

Procurement tracking for components not available in stock.

**Capabilities:**
- **Purchase requests** — auto-created when order conversion detects inventory shortage
- Linked to originating order and component product
- **Status lifecycle:** `pending` → `ordered` → `received`

### 6. Manufacturing

Work station definitions, product routings, and work order execution.

**Capabilities:**
- **Work stations** — named manufacturing stations with sequence ordering
- **Product routings** — ordered sequence of stations defining the manufacturing process per product
- **Work orders** — auto-created during order conversion for products with routings
- **Station advancement** — move work orders through their routing; logs operator, timestamps, and notes at each step
- **BOM revision snapshot** — work orders capture the approved BOM revision at creation time for traceability

### 7. Shipping

Shipment tracking with automatic invoice generation.

**Capabilities:**
- Shipment creation with carrier, tracking number, and shipping account
- **Auto-invoice** — creating a shipment automatically generates an invoice and sets order status to `shipped`

### 8. Invoices

Financial document management tied to shipments.

**Capabilities:**
- Auto-generated invoice number (`INV-YYYYMM-NNNN`)
- Line items mirrored from order with subtotal, tax, and total calculation
- **Status lifecycle:** `draft` → `sent` → `paid`

### 9. Authentication & Roles

JWT-based authentication with role-based onboarding segmentation.

**Capabilities:**
- User registration and login with email/password (bcrypt hashing)
- JWT tokens (HS256, 24h expiry) with role claim
- Three roles: `admin` (full access), `engineer` (products/manufacturing focus), `sales` (quotes/orders/shipping focus)
- Token interceptor on all frontend API calls

### 10. Onboarding System

AI-powered onboarding with three complementary layers.

**Smart Empty States:**
- Every list page shows contextual guidance when empty (what the page is for, where it fits in the workflow, action to get started)
- Workflow hints explain prerequisites (e.g., "Win a quote first, then convert it to generate orders")

**Onboarding Checklist:**
- Role-filtered milestone tracker in the sidebar (e.g., engineers see "Create your first product", sales see "Create your first quote")
- Auto-detects milestone completion by querying the database
- Clicking an incomplete milestone opens the AI copilot with a pre-filled prompt
- Dismissible per user

**AI Copilot:**
- Claude API-powered chat widget (floating button → right-side drawer)
- **Explain mode:** answers questions about ERP concepts, guides through workflows
- **Action mode:** creates products, BOMs, quotes, orders, stations, shipments via Claude tool use — always asks for confirmation before modifying data
- Dynamic system prompt includes user role, current page, and live application state (data counts, conditional hints)
- SSE streaming for real-time responses
- Conversation persistence across page navigations
- 12 integrated tools covering all domain operations

---

## Key Business Workflows

### Quote-to-Order (the core workflow)

```
Create Quote → Add Line Items → Advance Status (draft → review → approved → sent → won)
  → Convert to Order
    → Create Order + OrderLineItems
    → Traverse multi-level BOM for all components
    → Reserve available inventory (InventoryReservation)
    → Create PurchaseRequests for shortages
    → Create WorkOrders for products with routings (snapshot BOM revision)
```

### Manufacturing Execution

```
Work Order (queued) → Advance through stations → Log each step → Complete
  Each step records: operator, start/end timestamps, notes
```

### Ship & Invoice

```
Create Shipment → Auto-generates Invoice → Order marked "shipped"
  → Invoice sent → Invoice paid
```

---

## Data Model Highlights

- **Recursive BOM** with circular-reference detection
- **Decimal precision** (Numeric 14,4) on all financial and quantity fields
- **Cascade deletes** on child relationships (BOM items, line items, work order logs)
- **Unique constraints** on SKU, invoice number, product+revision pairs, product+balance
- **Status machines** with explicit allowed transitions on Quote, Order, WorkOrder, PurchaseRequest, and Invoice

---

## Frontend Pages

| Page            | Route              | Purpose                                      |
|-----------------|--------------------|----------------------------------------------|
| Login           | `/login`           | Sign in / register with role selection        |
| Products        | `/products`        | Finished goods & assemblies list              |
| Components      | `/components`      | Components & raw materials list               |
| Product Detail  | `/products/:id`    | Full product management (BOM, revisions, specs, compliance, cost, CSV import) |
| Quotes          | `/quotes`          | Quote list + create                           |
| Quote Detail    | `/quotes/:id`      | Line items, status transitions, convert to order |
| Orders          | `/orders`          | Order list with status filter                 |
| Order Detail    | `/orders/:id`      | Line items, reservations, work orders, shipments, invoices |
| Work Orders     | `/work-orders`     | Work order list, advance/complete actions     |
| Stations        | `/stations`        | Work station + routing management             |
| Inventory       | `/inventory`       | Balances + reservations                       |
| Purchasing      | `/purchasing`      | Purchase request tracking                     |
| Shipping        | `/shipping`        | Shipment list + create                        |
| Invoices        | `/invoices`        | Invoice list + status updates                 |

**Persistent UI components:**
- Sidebar: navigation + onboarding checklist (role-filtered) + user info/logout
- Copilot: floating chat button (bottom-right) → drawer with AI assistant
- Empty states: contextual guidance on all list pages when no data exists

---

## Deployment

### Local (Docker Compose)

```bash
make up        # Start all containers (backend, frontend, db)
make migrate   # Run Alembic migrations
make seed      # Populate test data
make reset     # Full clean restart (destroys volumes)
make down      # Stop containers
```

| Service  | URL                          |
|----------|------------------------------|
| Frontend | http://localhost:3000         |
| Backend Swagger | http://localhost:8000/docs |

### Production (Railway)

Two Railway services from the same repo, each with its own `railway.toml`:

| Service   | Build                  | Runtime               | Notes                                    |
|-----------|------------------------|-----------------------|------------------------------------------|
| Backend   | `backend/Dockerfile`   | FastAPI + Uvicorn     | Runs `alembic upgrade head` on startup   |
| Frontend  | `frontend/Dockerfile.prod` | Nginx (static build)  | Proxies `/api/*` → backend via `BACKEND_HOST` env var |
| Database  | Railway-managed        | PostgreSQL 15         | `DATABASE_URL` injected automatically    |

**Required environment variables on Railway:**

| Variable | Service | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | Backend | PostgreSQL connection (auto-injected by Railway) |
| `BACKEND_CORS_ORIGINS` | Backend | Frontend URL (e.g., `https://your-app.up.railway.app`) |
| `JWT_SECRET` | Backend | Secret key for JWT signing (use a strong random value in production) |
| `ANTHROPIC_API_KEY` | Backend | Claude API key for the AI copilot |
| `CLOUDFLARE_TURNSTILE_SECRET_KEY` | Backend | Turnstile CAPTCHA secret (optional) |
| `BACKEND_HOST` | Frontend | Internal Railway hostname of the backend service |
| `VITE_TURNSTILE_SITE_KEY` | Frontend | Turnstile site key (build-time arg, optional) |

**Nginx configuration** (`frontend/nginx.conf`):
- Proxies `/api/*` to backend (strips `/api` prefix)
- SSE streaming support (proxy buffering disabled) for AI copilot
- React Router SPA fallback (`try_files → /index.html`)
- Aggressive caching for Vite-hashed static assets

---

## Implementation Phases Completed

| Phase | Feature                                                          |
|-------|------------------------------------------------------------------|
| 1     | Product enrichment (category, revision, lifecycle, compliance)   |
| 2     | BOM revisions + work order BOM snapshot                          |
| 3     | BOM line enrichment + alternate components                       |
| 4     | Compliance document tracking                                     |
| 5     | Item type split (finished_good / assembly / component / raw_material) |
| 6     | BOM CSV import with column auto-detection                        |
| 7     | Authentication (JWT + roles) + smart empty states + onboarding checklist + AI copilot |
