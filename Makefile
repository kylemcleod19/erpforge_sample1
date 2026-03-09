.PHONY: up down migrate seed logs shell-backend shell-db

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	docker compose exec backend alembic upgrade head

seed:
	docker compose exec backend python -m app.seed

shell-backend:
	docker compose exec backend bash

shell-db:
	docker compose exec db psql -U erp -d erpdb

reset:
	docker compose down -v
	docker compose up -d --build
