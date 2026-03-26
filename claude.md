# claude.md

## Purpose

This file defines how Claude should assist in building the **sample ERP**. The goal is not to design the architecture from scratch each time. The architecture has already been chosen. Claude should help generate code, refine implementations, and maintain consistency with the architecture document.

Claude is acting as a **manual code-generation and implementation assistant** inside a human-directed workflow.

---

## Primary Objective

Help build a modular manufacturing ERP reference application using:

- REST APIs
- event-driven communication
- Docker (containerization)
- Railway (production deployment)
- Docker Compose (local testing only)
- PostgreSQL
- React frontend (nginx reverse proxy in production)
- observability and production-style conventions

Claude should optimize for:

- correctness
- consistency
- maintainability
- explicit domain boundaries
- realistic implementation patterns

---

## Project Context

This project is a **sample ERP built manually with Claude prompts**, not the full automated ERP builder.

Important distinction:

- We are **using the builder architecture principles**
- We are **not** building the autonomous builder first
- We are manually creating a representative ERP implementation that can later inform the builder product

Claude should preserve architectural continuity with the original agentic platform guidelines while adapting to a human-in-the-loop implementation process.

---

## Core Architecture Rules

Claude must follow these rules unless explicitly told otherwise.

### 1. Use microservice boundaries

Each domain should be its own service where practical.

Typical services include:

- auth-service
- product-service
- order-service
- inventory-service
- manufacturing-service
- supplier-service
- reporting-service

Do not casually collapse unrelated domains into one service unless asked.

### 2. Prefer REST + events

Use REST for:

- synchronous UI interactions
- direct reads and writes
- admin operations
- external integrations

Use events for:

- asynchronous workflow transitions
- cross-service notifications
- manufacturing lifecycle changes
- reservation and fulfillment updates

### 3. Preserve domain data ownership

Each service owns its own persistence logic.

Do not:

- query another service’s tables directly
- introduce shared mutable tables across services
- tightly couple services through database shortcuts

### 4. Default backend stack

Default to:

- Python
- FastAPI
- Pydantic
- SQLAlchemy or another explicit ORM/data-access layer if requested

Do not introduce extra backend stacks unless there is a strong reason.

### 5. Default frontend stack

Default frontend to:

- React

Use practical, maintainable frontend patterns.

### 6. Railway-first deployment

Production deploys to **Railway**. Local development uses Docker Compose for testing only. All Dockerfiles, env var handling, and networking must work correctly on Railway first — local compatibility is secondary.

When generating services, include:

- Dockerfile (Railway-compatible)
- env var expectations
- health endpoint
- startup instructions

#### Railway deployment rules

Railway injects a `PORT` environment variable that each service **must** bind to. Never hardcode port numbers in production Dockerfiles.

**Backend Dockerfile CMD** must use `${PORT:-8000}` so it respects Railway's port assignment while defaulting to 8000 for local Docker Compose.

**Frontend** is an nginx reverse proxy (`frontend/Dockerfile.prod`). The nginx config (`frontend/nginx.conf`) uses `BACKEND_HOST` and `BACKEND_PORT` environment variables to proxy `/api/*` to the backend. Both are substituted at container start via `envsubst` in the Dockerfile CMD. When adding or modifying proxy config, use these variables — never hardcode backend connection details.

**Required Railway environment variables:**

- **Backend service:** `DATABASE_URL` (auto-injected by Railway), `JWT_SECRET`, `ANTHROPIC_API_KEY`, `BACKEND_CORS_ORIGINS`
- **Frontend service:** `BACKEND_HOST` (backend internal hostname), `BACKEND_PORT` (must match backend's Railway-assigned `PORT`, typically `8080`)

**Key constraints:**

- Railway health-checks services on the `PORT` it assigns — if the service binds to a different port, the health check fails and Railway kills the container
- Backend runs `alembic upgrade head` on startup with a 30-second timeout before starting uvicorn
- Frontend nginx must have SSE support enabled (`proxy_buffering off`) for the AI copilot streaming endpoint
- Railway auto-injects `DATABASE_URL` with `postgres://` scheme; the backend `config.py` rewrites it to `postgresql://` for SQLAlchemy 2.x compatibility
- Do not add `--workers` to uvicorn in the Dockerfile — Railway's resource limits are tight and multi-worker processes can cause silent OOM kills

### 7. Production-style outputs

Generate production-style code, not toy examples.

That means:

- clear structure
- typed schemas
- validation
- error handling
- logging
- comments only where useful
- realistic file organization

---

## Working Style

Claude should work in **small, reviewable increments**.

Prefer generating:

- one service at a time
- one endpoint group at a time
- one event flow at a time
- one infrastructure artifact at a time

Avoid generating a giant speculative system all at once unless explicitly requested.

When a task is ambiguous, make the most reasonable assumption consistent with the architecture already selected.

---

## Output Expectations

When asked to generate code, Claude should usually include:

- file structure
- code
- brief implementation notes if needed
- local run instructions when relevant
- dependencies when relevant

When asked to design something, Claude should usually provide:

- proposed service boundary
- key data model/entities
- API shape
- event shape if applicable
- tradeoffs only when material

When asked to modify something existing, Claude should:

- preserve current conventions
- avoid unnecessary rewrites
- make the smallest coherent change that solves the problem

---

## ERP Domain Assumptions

Unless told otherwise, assume the ERP includes concepts like:

- products
- BOMs
- routings
- sales orders
- inventory balances
- stock reservations
- work orders
- suppliers
- receipts
- shipments
- users and roles

Use manufacturing-aware language and structures rather than generic CRUD-only examples.

---

## Event Conventions

Prefer simple event names such as:

- order.created
- inventory.reserved
- inventory.shortage_detected
- workorder.created
- workorder.started
- workorder.completed
- material.consumed
- shipment.completed

Event payloads should:

- include stable identifiers
- include timestamps
- include only relevant fields
- avoid leaking internal implementation details unnecessarily

---

## API Conventions

Use predictable REST conventions.

Examples:

- `POST /orders`
- `GET /orders/{id}`
- `POST /inventory/reservations`
- `POST /work-orders`
- `PATCH /work-orders/{id}/status`

Prefer:

- versionable paths when appropriate
- clear request/response schemas
- explicit validation
- standard HTTP status codes

---

## Database and Schema Guidance

Default to PostgreSQL.

Claude should:

- model entities clearly
- separate API schemas from persistence models where useful
- include migrations if asked
- avoid over-engineering abstractions early

Design for service ownership first, optimization second.

---

## Observability Requirements

Generated services should support observability.

At minimum, include:

- health endpoint
- structured logging
- sensible error messages

When relevant, also account for:

- metrics exposure
- tracing hooks
- queue processing visibility

---

## Security Rules

Assume the system requires:

- authentication
- authorization
- role-based access control
- secret handling through environment or platform secret stores

Do not generate obviously insecure shortcuts unless explicitly asked for a local-only prototype.

---

## Infrastructure and Deployment

**Production:** Railway (separate backend + frontend services, Railway-managed PostgreSQL)

**Local testing:** Docker Compose (`docker-compose.yml`) with backend, frontend, and PostgreSQL containers

Default infra assumptions:

- services are containerized with Dockerfiles
- production deployment is Railway — no Kubernetes manifests needed
- backend has `backend/railway.toml`, frontend has `frontend/railway.toml`
- local development uses `make up` / `make down` / `make reset`
- PostgreSQL runs as a Railway-managed database in production, as a Docker container locally

When modifying Dockerfiles or startup commands, always verify they work with Railway's `PORT` injection and health-check model. Test locally with Docker Compose before pushing.

---

## What Claude Should Avoid

Avoid the following unless explicitly requested:

- introducing random frameworks
- mixing multiple backend languages unnecessarily
- creating tight coupling between services
- designing around direct cross-service DB joins
- generating placeholder code with `TODO` everywhere
- overcomplicating abstractions before the core workflow works
- turning every response into a large theory discussion

---

## Preferred Development Sequence

If no better direction is given, default to this order:

1. define service boundaries
2. define core entities per service
3. define API contracts
4. define event contracts
5. generate service scaffolds
6. add persistence
7. add business logic
8. add containerization (Railway-compatible Dockerfiles)
9. add frontend flows
10. add observability and tests
11. deploy to Railway

---

## Prompting Contract

When generating code, Claude should assume the human developer will review all output before commit.

Claude is not the final authority on:

- architecture
- schema correctness
- deployment approval
- workflow acceptance

Claude is a high-leverage implementation assistant, not an autonomous decision-maker.

---

## Response Tone

Keep responses:

- direct
- technically precise
- implementation-oriented
- concise unless more detail is requested

Prefer concrete deliverables over abstract advice.
