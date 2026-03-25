# Claude Resources — Skills, Docs, and Configuration for ERPForge

This document catalogs every resource Claude can draw on when working in this project: skills, reference documentation, configuration, and memory.

---

## Skills (Slash Commands)

These are invocable via `/command-name` in conversation with Claude.

### `/design-review`

**Location:** `.claude/commands/design-review.md`

Runs a structured design review for a planned feature. Produces a 10-section document:

1. Problem Statement
2. Scope
3. Data Model Changes
4. API Changes
5. Business Logic
6. Frontend Changes
7. Event/Async Considerations
8. Migration & Compatibility
9. Open Questions
10. Acceptance Criteria

**When to use:** Before implementing a new feature or significant change. Helps align on scope and surface edge cases before writing code.

### `/write-docs`

**Location:** `.claude/commands/write-docs.md`

Generates documentation for a completed feature. Produces three documents:

1. **API Reference** → `docs/api/<feature-slug>.md`
2. **Migration Guide** → `docs/migrations/<migration-file-name>.md`
3. **Feature Summary / Changelog** → `docs/changelog/<YYYY-MM-feature-slug>.md`

**When to use:** After a feature is implemented and tested, to generate consistent documentation.

### `/simplify`

Built-in skill that reviews changed code for reuse, quality, and efficiency, then fixes any issues found.

**When to use:** After writing code, to catch over-engineering or missed reuse opportunities.

### `/claude-api`

Built-in skill for building apps with the Claude API or Anthropic SDK.

**When to use:** When modifying the AI copilot integration (`assistant_service.py`, `assistant_tools.py`) which uses the Anthropic Python SDK with streaming and tool use.

### `/loop`

Runs a prompt or slash command on a recurring interval (e.g., `/loop 5m /foo`).

**When to use:** For polling or recurring checks during development.

---

## Reference Documentation

### Architecture Blueprint

**Location:** `.claude/docs/sample_erp_manual_claude_architecture.md` (19 KB)

The comprehensive architecture document for the entire project. Covers:

- High-level architecture and communication model (REST + RabbitMQ)
- Technology stack decisions
- Service design standards
- Data architecture patterns
- Configuration and environment management
- Containerization and Kubernetes conventions
- CI/CD pipeline design
- Observability and monitoring
- Security model
- Future evolution path

**When to use:** When making architectural decisions, adding new services, or ensuring consistency with established patterns.

### BOM & Product Improvement Plan

**Location:** `.claude/bom_product_improvement_plan.md`

Structured plan organizing BOM improvements into 4 prioritized phases. All phases are now complete, but the document remains useful as a reference for the rationale behind current data model decisions.

### Discovery Questions Template

**Location:** `.claude/interview_templates/erp_bom_discovery_questions.md`

80 structured questions across 12 categories for ERP/MRP BOM discovery:
- Product Catalog, BOM Structure, Component Management, PCB/Electronics
- Revision/Change Management, Traceability, Inventory, Scrap/Overage
- Configuration/Variants, Manufacturing Context, Product Lifecycle, Documentation

**When to use:** When scoping new features that touch product or BOM domains — use as a checklist to surface requirements.

### Discovery Answers

**Location:** `.claude/interview_templates/bom_product_discovery_answers.md`

Captured requirements from the actual discovery process (2026-03-09). Documents specific decisions like:
- Standard SKU format, numeric revisions
- PCB reference designators required
- BOM versioning is critical
- Per-SKU traceability types (none, serial, lot)
- Selective compliance document tracking

**When to use:** When implementing BOM or product features, to understand the "why" behind current design choices.

---

## Design Documents

### Order Line Item SKU/Name Fix

**Location:** `.claude/designs/order-line-item-sku-name.md`

Documents the root cause analysis and fix for order line items not displaying product SKU/name. Records the pattern of adding `_enrich_order()` helpers for proper Pydantic serialization of ORM objects.

**When to use:** As a reference pattern when encountering similar serialization issues in other modules.

---

## Configuration

### Project Instructions

**Location:** `CLAUDE.md` (root)

The primary instruction set defining how Claude should work in this project:
- Architecture rules (microservice boundaries, REST + events, domain ownership)
- Default stacks (Python/FastAPI backend, React frontend)
- Working style (small reviewable increments)
- Output expectations (code, structure, implementation notes)
- ERP domain assumptions (products, BOMs, routings, orders, etc.)
- Event and API naming conventions
- Security, observability, and Kubernetes guidance

### Local Settings

**Location:** `.claude/settings.local.json`

Permissions whitelist for Claude operations:
- Allowed: `make reset`, Docker Compose commands, curl, WebFetch for Railway and documentation domains
- Everything else requires explicit approval

### Project Memory

**Location:** `~/.claude/projects/C--src-erpforge-sample1/memory/MEMORY.md`

Auto-maintained memory index tracking:
- Repository layout and architecture decisions
- Domain model summary
- Key business logic implementations
- Development commands and URLs
- Completion status of all 6 implementation phases

**When to use:** Automatically loaded into every conversation. Keeps Claude oriented on project state across sessions.

---

## Directory Map

```
.claude/
├── settings.local.json          # Claude permission settings
├── bom_product_improvement_plan.md  # Phase planning (complete)
├── commands/
│   ├── design-review.md         # /design-review skill
│   └── write-docs.md            # /write-docs skill
├── designs/
│   └── order-line-item-sku-name.md  # Design decision record
├── docs/
│   └── sample_erp_manual_claude_architecture.md  # Architecture blueprint
└── interview_templates/
    ├── erp_bom_discovery_questions.md  # Discovery template
    └── bom_product_discovery_answers.md  # Captured requirements

CLAUDE.md                        # Project-level instructions (root)
```

---

## How to Use These Resources Effectively

| Task | Resource to Use |
|------|----------------|
| Plan a new feature | `/design-review` + architecture doc |
| Scope BOM/product work | Discovery questions + answers |
| Write code | `CLAUDE.md` conventions + architecture doc |
| Review written code | `/simplify` |
| Document a completed feature | `/write-docs` |
| Understand past decisions | Design docs + memory + discovery answers |
| Check project state | Memory (auto-loaded) |
