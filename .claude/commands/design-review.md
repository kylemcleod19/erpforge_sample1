You are helping plan a new feature for the ERPForge sample ERP system (FastAPI monolith + React frontend). Conduct a structured design review for the following feature request:

**Feature:** $ARGUMENTS

---

Work through each section below. Ask clarifying questions using AskUserQuestion where requirements are ambiguous before filling in answers. Once you have enough context, produce the complete design document.

## 1. Problem Statement
- What business problem does this solve?
- Who uses it and how often?
- What breaks or is missing today?

## 2. Scope
- What is in scope for this implementation?
- What is explicitly out of scope?
- Any phasing (MVP now, full later)?

## 3. Data Model Changes
- New tables or columns required?
- Changes to existing tables?
- Alembic migration needed? (new migration file name: `000N_<short_description>.py`)
- Which SQLAlchemy models in `backend/app/models/` are affected?

## 4. API Changes
List every new or modified endpoint:
- Method + path (follow existing conventions in `backend/app/routers/`)
- Request schema (Pydantic model name, key fields)
- Response schema (Pydantic model name, key fields)
- Auth/permission implications (currently none — note if this should change)
- Error cases and HTTP status codes

## 5. Business Logic
- Which service file handles this? (`backend/app/services/`)
- New service file needed?
- Key algorithms or rules to implement
- Edge cases that need explicit handling

## 6. Frontend Changes
- Which pages are affected? (`frontend/src/pages/`)
- New page needed?
- New API helper needed? (`frontend/src/api/`)
- Key UI interactions (modals, tables, forms, etc.)

## 7. Event / Async Considerations
- Does this trigger or consume any async events?
- If yes: event name, payload fields, producer, consumer

## 8. Migration & Compatibility
- Does this change existing API contracts?
- Does this require data backfill?
- Any impact on existing Alembic migrations (0001–0005)?

## 9. Open Questions
List unresolved decisions or dependencies. Flag anything that needs product or architecture sign-off.

## 10. Acceptance Criteria
Write concrete, testable criteria:
- [ ] API returns correct response for happy path
- [ ] API handles error cases with correct status codes
- [ ] Frontend renders new/changed UI correctly
- [ ] Existing tests still pass
- [ ] New tests cover the core logic
- [ ] Documentation updated (API docs, MEMORY.md if architecture changed)

---

After completing the review, ask if the user wants to save this as a design document to `.claude/designs/<feature-slug>.md`.
