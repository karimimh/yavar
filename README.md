# Yavar (یاور)

Persian-first personal action agent. P0 MVP is implemented against **sandbox
adapters** labeled آزمایشی. This is not a live Iranian provider integration.

## How to run

```bash
cp .env.example .env
make up        # Docker: web :3000, backend :8000, postgres, redis, celery
make logs      # OTP codes print as: [YAVAR SMS] to=+98… body=YAVAR OTP 123456
```

- Frontend: http://localhost:3000
- Backend health: http://localhost:8000/api/health/
- Django admin: http://localhost:8000/admin/

Sign in with an Iranian mobile number. The console SMS provider logs the OTP in
the **backend** container output (`make logs` or `docker compose logs backend`).
Sign-in OTPs do not consume reminder SMS allowance.

If you already had a Postgres volume from the empty foundation, the custom user
model needs a clean database:

```bash
docker compose down
docker volume rm yavar_postgres_data
docker compose up -d --build
```

## What is real vs sandbox

| Area | Status |
|---|---|
| Accounts, OTP, sessions, tasks, reminders, agenda, approvals, entitlements | Real in-app behavior |
| Flight search (two sources), electricity bill, local service request, public research | Deterministic **sandbox** adapters (`PROVIDER_MODE=sandbox`) |
| Product Pro checkout (۲۹۹٬۰۰۰ تومان / ۳۰ روز) | Sandbox redirect + verify + inquiry |
| LLM | Optional; without `LLM_API_KEY` reminders/task CRUD still work; vision/research fallbacks stay honest |
| SMS gateway | `ConsoleSmsProvider` (logs only) |

Sandbox results are labeled آزمایشی. They are never presented as a named live
Iranian brand or a real ticket/payment receipt.

## Tests

```bash
make test           # Vitest + pytest
make test-backend   # 160 passed, 11 skipped (live-provider pending)
make test-web
make lint
```

Demo user (still labeled sandbox): `make seed-demo`

## Architecture

Django modular monolith (`backend/apps/*`) is the system of record. Next.js
(`apps/web`) talks to `NEXT_PUBLIC_API_URL` with session cookies. Playwright
fixture for the nonbinding form lives in `automation/browser/browser_worker/`.
