# Yavar

Yavar is a personal assistant project. **This repository currently contains only the
project foundation** — the development environment, infrastructure configuration, and
tooling. No product functionality has been implemented yet.

## Repository structure

```text
yavar/
├── apps/
│   └── web/                # Next.js frontend (App Router, TypeScript)
├── backend/                # Django backend (modular monolith)
│   ├── config/             # Project config: settings, urls, celery, wsgi/asgi
│   │   └── settings/       # base / development / production settings
│   └── apps/
│       └── core/           # Infrastructure app (health endpoint, pgvector migration)
├── automation/
│   └── browser/            # Future browser worker (Playwright + Chromium)
├── docker/                 # Dockerfiles and Postgres init script
├── docs/                   # Project documentation
├── docker-compose.yml      # Development stack
├── .env.example            # Environment variable template
└── Makefile                # Common development commands
```

## Technology stack

| Layer | Technology |
| --- | --- |
| Frontend | Next.js 16, React 19, TypeScript (strict), Tailwind CSS 4, shadcn/ui, TanStack Query, React Hook Form, Zod |
| Backend | Python 3.13, Django 5.2 LTS, Django REST Framework, Pydantic |
| Database | PostgreSQL 17 with pgvector |
| Queue | Redis 8, Celery 5.6, Celery Beat (database scheduler) |
| Browser automation | Playwright for Python + Chromium (environment only) |
| Tooling | uv, Ruff, pytest, ESLint, Prettier, Vitest |

## Prerequisites

- Docker (with Compose v2) — for the full stack
- Node.js 22+ and npm — for running the frontend locally
- Python 3.13 and [uv](https://docs.astral.sh/uv/) — for running the backend locally

## Environment setup

```bash
cp .env.example .env
```

Adjust values as needed. The defaults work for local development. Never commit `.env`.

## Local development

### Full stack with Docker (recommended)

```bash
make up        # build and start everything
make logs      # tail logs
make down      # stop everything
```

Services started by `docker compose up`:

| Service | Purpose | Port |
| --- | --- | --- |
| `web` | Next.js dev server | 3000 |
| `backend` | Django dev server (runs migrations on start) | 8000 |
| `celery-worker` | Celery worker | — |
| `celery-beat` | Celery Beat scheduler | — |
| `browser-worker` | Playwright/Chromium environment (idle) | — |
| `postgres` | PostgreSQL 17 + pgvector | 5433 (host) → 5432 |
| `redis` | Redis broker/result backend | 6379 |

Once running:

- Frontend: <http://localhost:3000>
- Backend health check: <http://localhost:8000/api/health/>

### Running pieces individually (outside Docker)

Requires local PostgreSQL and Redis, or start just those via
`docker compose up -d postgres redis`.

```bash
make install   # install all dependencies
make web       # Next.js dev server
make backend   # Django dev server
make migrate   # run Django migrations
make worker    # Celery worker
make beat      # Celery Beat
```

## Database migrations

```bash
make migrate
# or inside Docker:
docker compose exec backend python manage.py migrate
```

The initial migration enables the `vector` (pgvector) extension. It is also enabled by
`docker/postgres/init.sql` when the Postgres volume is first created.

## Testing

```bash
make test           # everything
make test-web       # frontend (Vitest)
make test-backend   # backend (pytest, needs Postgres running)
```

## Linting and formatting

```bash
make lint      # ESLint + tsc --noEmit + Ruff
make format    # Prettier + Ruff format
```

## Notable configuration

- **Django settings** are split into `base.py`, `development.py`, and `production.py`
  under `backend/config/settings/`, selected via `DJANGO_SETTINGS_MODULE`. All secrets
  and connection details come from environment variables.
- **Celery** uses Redis as broker and result backend; Beat uses the
  `django-celery-beat` database scheduler. No tasks are defined yet.
- **The frontend** is prepared for future Persian/RTL support (shadcn/ui initialized
  with RTL support enabled); the UI is currently a neutral placeholder only.
- **The browser worker** (`automation/browser/`) only verifies that Playwright and
  Chromium work. No automation is implemented.
