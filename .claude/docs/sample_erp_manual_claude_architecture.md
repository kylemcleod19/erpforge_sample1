# Sample ERP via Manual Claude Prompting

## Architecture Document

## 1. Purpose

This document defines the architecture for building a **sample ERP** using the same core principles as the Agentic Platform Builder, but with **manual Claude code prompting** instead of a fully automated builder.

The goal is to prove that the architectural model works even when the system is assembled incrementally through developer-guided prompting, review, and manual integration.

This approach should:

- preserve the same modular service boundaries
- use the same deployment and observability standards
- support iterative development through prompt-driven code generation
- allow a developer to orchestrate implementation decisions manually
- create a realistic reference ERP that can later inform the full builder product

The system remains focused on:

- modularity
- observability
- automation where practical
- AI-assisted development
- portability from local development to cloud production

---

## 2. Architectural Intent

The original builder architecture assumes an orchestrated agent layer that can generate, deploy, and evolve manufacturing applications automatically. In this sample ERP, those architectural decisions remain intact, but the **generation path changes**.

Instead of a Platform Builder Agent and Service Generator Agent automatically creating services, a developer uses Claude manually to:

- define service contracts
- generate service scaffolds
- generate API endpoints
- generate schemas and workflows
- generate infrastructure manifests
- iterate on implementation details

This keeps the architecture stable while changing the delivery mechanism from **agent-orchestrated generation** to **human-directed AI coding**. The result is a reference implementation that still follows the original microservice, event-driven, containerized, Kubernetes-based design. fileciteturn1file1L29-L53 fileciteturn1file2L114-L148

---

## 3. Scope of the Sample ERP

The sample ERP should be intentionally limited but representative. It should cover the most important manufacturing workflow patterns without trying to implement a full enterprise suite.

Recommended initial domains:

- Orders
- Inventory
- Work Orders / Manufacturing
- Products / BOMs
- Suppliers
- Authentication / Users
- Basic Reporting

Optional later domains:

- Purchasing
- Shipping
- Quality
- Customer management
- Accounting integrations

The sample ERP is a **reference platform**, not a one-off demo. It should be built as though it could later become:

- a template for future ERP generation
- a testing ground for prompt patterns
- a baseline implementation for the full builder product

---

## 4. High-Level Architecture

The system follows a **microservices architecture**. Each domain is implemented as an independently deployable service with its own API, internal logic, and data ownership. This preserves the original architecture’s service isolation, loose coupling, and scalability model. fileciteturn1file1L29-L53

Each service should:

- run as a container
- expose REST APIs
- emit domain events where appropriate
- own its own persistence layer
- be deployable independently

Example service set:

- `auth-service`
- `product-service`
- `order-service`
- `inventory-service`
- `manufacturing-service`
- `supplier-service`
- `reporting-service`
- `api-gateway` or frontend BFF if needed

The frontend should be a separate React application that consumes the APIs and presents a cohesive ERP UI. The architecture may optionally include a lightweight API gateway for routing, auth enforcement, and request normalization.

---

## 5. Communication Model

The sample ERP uses the same **dual communication model** as the builder architecture:

### 5.1 REST APIs

REST is used for:

- user interface interactions
- synchronous reads and writes
- administrative operations
- external system integrations
- canonical master-data access

REST standards:

- JSON payloads
- OpenAPI definitions
- versioned endpoints
- predictable error contracts
- request validation at the service boundary

Examples:

```text
POST /orders
GET /orders/{id}
POST /inventory/reservations
GET /products/{id}
POST /work-orders
```

### 5.2 Event-Driven Messaging

Events are used for:

- cross-service state changes
- asynchronous workflow progression
- domain notifications
- long-running manufacturing processes
- auditability of key business transitions

Examples:

```text
order.created
inventory.reserved
workorder.created
workorder.started
workorder.completed
purchaseorder.issued
shipment.completed
```

RabbitMQ is the preferred initial broker because it is relatively simple to run locally and is suitable for a reference implementation. Kafka can be evaluated later if the event model becomes heavier or requires more advanced replay semantics.

This preserves the original architectural principle that synchronous workflows should use REST and asynchronous process coordination should use events. fileciteturn1file1L77-L128

---

## 6. Technology Stack

The sample ERP should stay close to the original hybrid-stack recommendation, but narrow the number of technologies enough to keep development manageable.

### Recommended initial stack

- **Backend services:** Python with FastAPI
- **Frontend:** React
- **Database:** PostgreSQL per service where practical, or one PostgreSQL instance with separate schemas/databases during early development
- **Event broker:** RabbitMQ
- **Containerization:** Docker
- **Orchestration:** Kubernetes (Kind or Minikube locally)

### Why this stack

Python + FastAPI is the best fit for prompt-driven development because:

- service scaffolds are quick to generate
- validation with Pydantic is clear
- OpenAPI generation is built in
- the code is readable for iterative review
- AI-assisted edits are usually effective in this stack

React remains the preferred frontend framework in continuity with the original design. fileciteturn1file1L132-L176

### Technology simplification principle

The sample ERP should minimize unnecessary polyglot complexity. Even though the original architecture supports both Python and Node.js services, the sample ERP should default to one primary backend stack unless there is a strong reason to diversify. This keeps Claude prompting more consistent and reduces integration overhead.

---

## 7. Service Design Standards

Each service should conform to a standard template.

### Required service components

Every service should include:

- clear domain ownership
- FastAPI app entrypoint
- route layer
- schema / DTO definitions
- domain or application service layer
- persistence or repository layer
- health endpoint
- structured logging
- Dockerfile
- environment configuration
- OpenAPI output
- test skeletons

### Service responsibilities

Each service must:

- own its internal domain logic
- expose its own API surface
- publish domain events when meaningful state changes occur
- subscribe only to events it truly needs
- avoid direct database access into other services

These standards preserve the original microservice boundary principles and localize failures, deployment risk, and schema evolution. fileciteturn1file1L56-L73

---

## 8. Data Architecture

The sample ERP should follow **domain data ownership**.

Each service owns its own tables and migration lifecycle. Even if early development uses a shared PostgreSQL server for convenience, service boundaries must still be maintained logically through:

- separate databases, or
- separate schemas with strict ownership conventions

Example ownership:

| Service | Owns |
|---|---|
| Product Service | products, BOMs, routings |
| Order Service | sales orders, order lines |
| Inventory Service | stock balances, reservations, movements |
| Manufacturing Service | work orders, production runs, completions |
| Supplier Service | suppliers, supplier-item relationships |
| Auth Service | users, roles, permissions |

### Master data

A small number of services should act as authoritative systems of record.

Examples:

- Product Service = canonical product and BOM definitions
- Auth Service = canonical user identity and access model
- Supplier Service = canonical supplier records

Other services should retrieve this information via APIs or events rather than direct table access. This remains directly aligned with the original architecture. fileciteturn1file2L1-L27

---

## 9. Configuration Strategy

The sample ERP should support layered configuration so that the same codebase can run locally, in staging, and later in production.

Configuration layers:

1. environment configuration
2. service configuration
3. business workflow configuration

Examples:

- default warehouse rules
- reservation behavior
- work order release policies
- low-stock thresholds
- supplier lead-time assumptions

Configuration must be:

- versioned
- validated
- observable
- overrideable by environment

Initially, configuration can live in environment variables plus version-controlled YAML or JSON config files. Later, selected workflow configuration may move into database-backed admin tools.

This remains consistent with the original architecture’s runtime configurability requirement. fileciteturn1file3L165-L185

---

## 10. Containerization and Orchestration

All services must run in Docker containers. Each service should include:

- a Dockerfile
- health checks
- environment variable handling
- startup command definitions
- log output to stdout/stderr

Local orchestration should use Kubernetes from the beginning, preferably via **Kind** for local repeatability. Minikube is also acceptable.

Why Kubernetes this early:

- it matches the target architecture
- it forces explicit service boundaries
- it tests deployment assumptions early
- it makes the sample ERP a better proving ground for the future builder

The cloud target remains AWS EKS, with the possibility of GKE or AKS later. fileciteturn1file1L179-L225

---

## 11. CI/CD and Development Flow

A dedicated enterprise CI/CD platform is not required for the initial version.

Initial delivery workflow:

- Claude generates or edits code through manual prompts
- developer reviews and patches the output
- local tests run via scripts or Make targets
- Docker images are built locally
- images are deployed into local Kubernetes
- smoke tests verify service health and workflows

Suggested automation:

- `make test`
- `make lint`
- `make build`
- `make up`
- `make deploy-local`
- `make seed-data`

Future CI/CD can move to self-hosted Jenkins or GitLab CI/CD, preserving the original architecture direction. fileciteturn1file2L55-L70

---

## 12. Observability

The sample ERP should include observability from the start.

### Metrics

Use:

- Prometheus
- Grafana

Track at minimum:

- request latency
- error rates
- throughput
- queue depth
- event processing time
- container health
- database connectivity

### Logging

Use structured logs in JSON format where practical.

Preferred longer-term stack:

- Elasticsearch
- Logstash or Fluent Bit
- Kibana

For local development, simpler log aggregation is acceptable as long as logs are structured and searchable.

Observability is not optional, because the sample ERP is also meant to teach the future builder how services behave in practice. fileciteturn1file2L74-L110

---

## 13. Security

The sample ERP should implement a minimal but real security model.

Required standards:

- API authentication
- role-based access control
- encrypted secrets handling
- service-to-service trust model
- audit logging for sensitive operations

Recommended initial implementation:

- JWT-based authentication
- role and permission claims
- Kubernetes secrets or local secret injection for development
- RBAC enforced in the auth layer and key service endpoints

Security should not be deferred entirely just because this is a sample. The reference implementation should demonstrate how authorization works across ERP workflows. fileciteturn1file2L152-L165

---

## 14. Sample Domain Workflow

A representative end-to-end workflow should be implemented to validate the architecture.

### Example flow: sales order to manufacturing completion

1. user creates a sales order in the UI
2. order-service persists the order
3. `order.created` event is emitted
4. inventory-service checks stock and reserves available material
5. if stock is insufficient, manufacturing-service creates a work order
6. product-service provides BOM and routing data
7. work order progresses through statuses
8. inventory is consumed and finished goods are recorded
9. order status updates based on fulfillment progress
10. reporting-service exposes operational status

This workflow proves the architecture across:

- REST interactions
- event-driven coordination
- domain ownership
- UI integration
- observability
- manual Claude-generated code across multiple services

---

## 15. Manual Claude Prompting Workflow

Because this ERP is being built manually with Claude rather than through the builder, prompt discipline becomes part of the architecture.

### Prompting model

The developer should use Claude to generate artifacts in small, reviewable units:

- service skeletons
- API route files
- database models
- migration scripts
- event publisher/subscriber code
- Kubernetes manifests
- frontend components
- integration tests

### Prompting standards

Prompts should:

- specify the domain and service boundary clearly
- request production-style code, not toy examples
- require typed schemas and validation
- require health checks, logging, and tests
- prohibit cross-service database coupling
- require Docker and local run instructions when appropriate
- preserve consistency with existing folder conventions

### Human review rule

Claude output is always subject to developer review before commit. The human remains the final orchestrator for:

- architecture decisions
- schema acceptance
- API contract approval
- integration sequencing
- deployment validation

In other words, the agentic layer is replaced by a **manual human-in-the-loop orchestration model**, not by abandoning architectural rigor.

---

## 16. Repository Structure

A monorepo is recommended for the sample ERP to simplify local development.

Example structure:

```text
sample-erp/
  apps/
    frontend/
  services/
    auth-service/
    product-service/
    order-service/
    inventory-service/
    manufacturing-service/
    supplier-service/
    reporting-service/
  infra/
    k8s/
    docker/
    rabbitmq/
    postgres/
    monitoring/
  docs/
    architecture/
    prompts/
  scripts/
  Makefile
  claude.md
```

A monorepo is the best early-stage choice because:

- prompts can reference existing code easily
- service conventions are easier to standardize
- local orchestration is simpler
- architectural drift is easier to manage

---

## 17. Non-Goals

The first sample ERP should not attempt to solve everything.

Out of scope for v1:

- full financial accounting
- deeply customizable workflow builders
- advanced MRP optimization logic
- multi-tenant SaaS isolation
- complex external EDI integrations
- enterprise-grade HA topology
- no-code service generation

The objective is architectural validation and a working reference ERP, not feature completeness.

---

## 18. Future Evolution

Once the sample ERP is stable, it can evolve into one of three paths:

1. **Reference implementation** for demonstrating the builder concept
2. **Prompt library baseline** for consistent Claude-generated services
3. **Migration seed** for a future automated builder/orchestrator

Future improvements may include:

- prompt templates per service type
- reusable code generation checklists
- auto-generated OpenAPI contract validation
- automated infrastructure provisioning
- deeper manufacturing planning logic
- migration from manual prompting to orchestrated generation

This mirrors the original architecture’s emphasis on future automation and AI-driven platform evolution. fileciteturn1file2L210-L223

---

## 19. Guiding Principles

This sample ERP must preserve the original architecture’s guiding principles even though implementation is manual.

Architecture decisions prioritize:

1. modularity
2. observability
3. automation where useful
4. AI-assisted development
5. cloud portability
6. explicit service boundaries
7. developer review over blind generation
8. reference-quality implementation over speed hacks

These principles are directly inherited from the original architecture and adapted for a manual Claude-driven workflow. fileciteturn1file2L221-L223 fileciteturn1file0L110-L118
