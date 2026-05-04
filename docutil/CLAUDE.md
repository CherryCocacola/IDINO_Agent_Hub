# DocUtil — Document Utilization System

RAG-based document management system with chatbot, search, and report generation.

## Tech Stack
- Backend: FastAPI (Python 3.12), SQLAlchemy 2 async, Pydantic v2, Celery + RabbitMQ
- Frontend: Next.js 16 (App Router), TypeScript, Tailwind CSS, shadcn/ui
- DB: PostgreSQL 17, Qdrant v1.16 (hybrid vector search), Redis 7, MinIO
- LLM: OpenAI GPT-4o + text-embedding-3-small (multi-provider ready)
- Infra: Docker Compose, Nginx, Prometheus + Grafana + Loki

## Module Structure (MUST follow)
Backend modules live in `backend/app/modules/{name}/` with ONLY these files:
- router.py, service.py, schemas.py, models.py, utils.py, constants.py, exceptions.py
- NO other filenames (no helpers.py, handler.py, controller.py)

## Commands
```bash
# Dev (Windows)
cd D:\workspace\document_utilization
docker compose up -d --build
docker exec docutil-api alembic upgrade head

# Lint (Windows)
cd backend && ruff check . && ruff format .
cd frontend && npx eslint . && npx prettier --check .

# Test (Windows)
cd backend && pytest tests/ -v
cd frontend && npm run build

# Structure lint (Windows)
python scripts\lint_structure.py

# QA Tests (Windows)
scripts\qa.bat               # Full QA (~5 min)
scripts\qa_quick.bat         # Quick QA (~2 min)

# QA Tests (Ubuntu server)
bash scripts/qa.sh           # Full QA (~5 min)
bash scripts/qa_quick.sh     # Quick QA (~2 min)

# Deploy to Ubuntu server
python scripts/deploy_to_server.py
```

## Critical Rules
- ALL LLM calls go through `app/integrations/llm/client.py` — never import openai SDK directly
- ALL MinIO access through `MinIOService` — never import minio directly
- ALL config from `app.core.config.settings` — never hardcode URLs, keys, or ports
- Korean filenames: always use RFC 5987 encoding (`filename*=UTF-8''...`)
- Python: absolute imports only (`from app.modules.xxx`), no relative imports
- API responses: snake_case in Python, camelCase mapping at frontend boundary
- DB schema changes: always create Alembic migration
- Commit messages: `[module] description in Korean`

## Server Notes
- Ubuntu server (192.168.10.39): Xeon E5-2620 v4 — does NOT support x86-64-v2
- MinIO: must use `quay.io/minio/minio:RELEASE.2023-09-04T19-57-37Z` (not latest)
- NumPy: must pin `numpy<2.0.0`
- After deploy: always run `sed` to fix MinIO image version in docker-compose.yml

See .claude/rules/ for architecture principles, anti-patterns, and domain model.
