# claude.md

## Purpose

This file defines how Claude should assist in building the **sample ERP**. The goal is not to design the architecture from scratch each time. The architecture has already been chosen. Claude should help generate code, refine implementations, and maintain consistency with the architecture document.

Claude is acting as a **manual code-generation and implementation assistant** inside a human-directed workflow.

---

## Primary Objective

Help build a modular manufacturing ERP reference application using:

- microservices
- REST APIs
- event-driven communication
- Docker
- Kubernetes
- PostgreSQL
- RabbitMQ
- React frontend
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

### 6. Container-first mindset

Services should be designed to run in Docker and deploy into Kubernetes.

When generating services, include:

- Dockerfile
- env var expectations
- health endpoint
- startup instructions

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

## Kubernetes and Infra Guidance

Default local orchestration to:

- Kind or Minikube

Default infra assumptions:

- services are containerized
- manifests live in `infra/k8s/`
- local development may use port-forwarding or ingress
- RabbitMQ and PostgreSQL may run in-cluster or through local containers

When asked for infra files, generate realistic Kubernetes YAML, not pseudo-config.

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
8. add containerization
9. add Kubernetes manifests
10. add frontend flows
11. add observability and tests

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
