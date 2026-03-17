You are generating documentation for a completed feature in the ERPForge sample ERP system. The feature to document is:

**Feature:** $ARGUMENTS

---

Before writing, read the relevant source files to understand what was actually built — do not guess. Check:
- Affected routers in `backend/app/routers/`
- Affected schemas in `backend/app/schemas/`
- Affected services in `backend/app/services/`
- Affected models in `backend/app/models/`
- Affected frontend pages in `frontend/src/pages/`
- Any new Alembic migration in `backend/alembic/versions/`
- The design document in `.claude/designs/` if one exists

Produce the following three documents:

---

## Document 1: API Reference
**File:** `docs/api/<feature-slug>.md`

Include:
- Overview (1–2 sentences: what this API does and why)
- For each new or changed endpoint:
  - Method + path
  - Description
  - Request body (field name, type, required/optional, description)
  - Response body (field name, type, description)
  - Example request (curl)
  - Example response (JSON)
  - Error responses (status code + body)

Use this format for each endpoint:

```
### POST /example/{id}/action

Creates or updates X for a given Y.

**Request**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name  | string | yes | ... |

**Response** `200 OK`
| Field | Type | Description |
|-------|------|-------------|
| id    | int  | ... |

**Errors**
- `404` — resource not found
- `422` — validation error

**Example**
\`\`\`bash
curl -X POST http://localhost:8000/example/1/action \
  -H "Content-Type: application/json" \
  -d '{"name": "test"}'
\`\`\`
```

---

## Document 2: Migration Guide
**File:** `docs/migrations/<migration-file-name>.md`

Include:
- Migration file name and what it adds/changes
- Tables and columns affected
- How to apply: `make migrate` (or `alembic upgrade head`)
- How to roll back: `alembic downgrade -1`
- Any data backfill steps required (with SQL if applicable)
- Impact on existing data (nullability, defaults, etc.)

If no migration was needed, note that explicitly and skip this file.

---

## Document 3: Feature Summary (Product Changelog)
**File:** `docs/changelog/<YYYY-MM-feature-slug>.md`

Write this for a technical audience (developers and product managers, not end users). Include:
- **What changed**: bullet list of capabilities added or modified
- **Why**: the business problem this solves
- **Breaking changes**: any API or schema changes that affect existing integrations (list "None" if none)
- **Known limitations**: anything deferred or intentionally out of scope
- **How to test**: step-by-step to verify the feature works end-to-end in a local environment

---

After writing all documents:
1. List the files created
2. Ask if `MEMORY.md` (in `C:\Users\mcleo\.claude\projects\C--src-erpforge-sample1\memory\`) should be updated to reflect new architecture, endpoints, or conventions introduced by this feature
