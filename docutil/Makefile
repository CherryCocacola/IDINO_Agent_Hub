.PHONY: up down build logs test-backend test-frontend lint env clean

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

test-backend:
	cd backend && python -m pytest --tb=short -q

test-frontend:
	cd frontend && npx vitest run

test: test-backend test-frontend

lint:
	cd backend && ruff check . && ruff format --check .
	cd frontend && npm run lint

env:
	cp .env.example .env

clean:
	docker compose down -v --remove-orphans

restart:
	docker compose restart

status:
	docker compose ps
