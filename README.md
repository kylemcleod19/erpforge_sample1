# ERPForge — Sample ERP

A manufacturing ERP reference implementation (FastAPI monolith + React frontend) built manually, one prompt at a time, as a working reference while developing an agentic ERP-builder platform.

It covers a realistic manufacturing workflow — products & BOMs, quotes, orders, inventory, purchasing, work orders, shipping, and invoicing — plus JWT auth and an AI copilot (Claude API) with tool use.

See [ERPForge_Overview.md](ERPForge_Overview.md) for a full module-by-module breakdown, and [Claude_Resources.md](Claude_Resources.md) for how this project was built with Claude Code.

## Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic
- **Frontend:** React 18, Vite, Ant Design v5
- **Database:** PostgreSQL 15
- **Deploy:** Railway (production), Docker Compose (local only)

## Running locally

Requires Docker and Docker Compose.

```bash
cp .env.example .env
# edit .env and set a real JWT_SECRET (required — the app won't start without one)
make up        # docker compose up -d --build
make migrate   # alembic upgrade head
```

- Backend (Swagger UI): http://localhost:8000/docs
- Frontend: http://localhost:3000

Other commands: `make down`, `make reset` (drops volumes and rebuilds), `make logs`, `make shell-backend`, `make shell-db`.

## License

No license is granted. This code is shared publicly for reference and portfolio purposes only — you may read it, but you may not copy, modify, or redistribute it without permission.
