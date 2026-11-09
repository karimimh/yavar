# Yavar (یاور)

**A Persian-language personal "action agent" that turns everyday requests into tracked tasks, and only acts on your behalf after you explicitly approve each step.**

Yavar ("helper" in Persian) is built for users in Iran. You type a request in
Persian, for example *"remind me tomorrow at 10 to take my medicine"*, *"find
a flight from Tehran to Shiraz under 3 million toman"* or *"check my
electricity bill"*. Yavar splits it into separate tasks, researches or
prepares each one, and stops for exact-action approval before anything is
submitted externally. The whole UI is Persian and right-to-left, with Jalali
(Persian calendar) dates and toman amounts.

> **Status: MVP on sandbox providers.** The core product flows work end to end,
> but every external provider (flights, bills, service requests, payments,
> SMS) is a deterministic **sandbox adapter**. The UI labels these results
> آزمایشی ("experimental/sandbox"). No live Iranian provider is integrated,
> and the app never presents sandbox data as a real ticket, payment or
> booking.

## Features

Implemented:

- **Phone + OTP sign-in.** Iranian mobile numbers, HMAC-hashed one-time codes,
  rate-limited requests and verification attempts, HTTP-only session cookie
  with CSRF. In development the SMS provider prints codes to the backend log.
- **Conversation to tasks.** A Persian intent parser splits one message into
  up to three independent tasks (more triggers a batch proposal). Each task
  has its own deliverable, plan, execution state and event history. It also
  catches OTPs or passwords pasted into chat and warns the user instead of
  using them.
- **Reminders and agenda.** One-off, daily and weekly reminders on a Jalali
  calendar with a Saturday-first week. Due reminders are fired by a
  Celery Beat tick into an in-app inbox. When the user changes timezone,
  the app asks how to handle existing reminders.
- **Screenshot extraction (optional LLM).** Upload one JPEG/PNG/WebP and an
  OpenAI-compatible vision model drafts obligations from it. Drafts are never
  saved automatically. Without an API key the feature reports that it needs
  configuration and invents nothing.
- **Sourced comparisons.** Public-research comparisons (products, mobile vs.
  fixed internet packages, local services) with sources. The parser asks for
  clarification when a request is ambiguous (for example an implausible
  budget phrase), and quotes without a currency unit are marked unusable
  rather than guessed.
- **Domestic flight search.** Two sandbox sources, hard constraints (budget,
  time of day) kept separate from preferences, price re-check before
  handoff, and an honest "continue on the provider's site" handoff (no ticket
  purchase).
- **Electricity bill inquiry.** Consent before sharing the bill ID, inquiry,
  and a hard stop before payment. "Paid" is recorded only as user-reported.
- **Approval-gated service requests.** A non-binding service request (an
  oil-change appointment request as the sample) goes through a draft, then an
  exact-action approval preview. The approval is valid for 10 minutes and
  covers one submission. It is invalidated if any field changes, and
  timeouts become `outcome_unknown` with no blind retry.
- **Capability registry and coverage page.** Every external action checks a
  registry (`available`, `limited`, `temporarily_unavailable`,
  `not_supported`) before it is offered or run.
- **Plans and entitlements.** Free and Pro plans with task-run and SMS
  allowances. A run is reserved when work starts, consumed when the deliverable
  is produced, and restored on failure. Pro checkout uses a sandbox payment
  flow that keeps redirect, verify and inquiry as separate steps.
- **Privacy controls.** Data export, account deletion, attachment deletion,
  and scheduled purges of old screenshots and temporary identifiers.
- **Operator tools.** A staff-only `/ops` page and API to disable a
  capability, pause all external submissions, suspend an account, restore
  credits and view incident trails. Every operator action is audit-logged.

Not implemented / planned:

- Live integrations with real Iranian travel, utility, SMS and payment
  providers (tests for these exist and are skipped).
- LLM-driven intent planning. Intent extraction is currently rule-based, and
  the LLM client is only used for screenshot extraction.
- Wiring the Playwright worker into the backend request flow (see
  Architecture).
- Production deployment hardening. `config/settings/production.py` is a strict
  skeleton only.

## Architecture

```text
 Next.js web app (apps/web)  --session cookie + CSRF-->  Django REST API (backend)
   Persian RTL UI, TanStack Query                          modular monolith, system of record
                                                                 |
                       +-------------------+---------------------+------------------+
                       |                   |                     |                  |
                PostgreSQL 17        Redis (broker)       Celery worker/beat    Provider adapters
                (+ pgvector ext.)                         reminders, purges     sandbox by default
```

- **Backend:** a Django modular monolith with one app per domain (`accounts`,
  `conversations`, `tasks`, `approvals`, `reminders`, `notifications`,
  `memory`, `coverage`, `billing`, `research`, `travel`, `bills`, `requests`,
  `agent`, `operators`, `core`). The `agent` app holds intent extraction, the
  tool functions and the run loop. Tools are plain Python, and the language
  model cannot grant approvals, change the capability registry or mark an
  external action as successful.
- **Two separate status tracks.** A task's *execution state* (`queued`,
  `needs_approval`, `delivered`, `outcome_unknown`, ...) is stored separately
  from its *external outcome* (`prepared_only`, `request_received`,
  `user_reported_complete`, ...). This way a prepared handoff is never shown
  as a completed purchase.
- **Ports and adapters.** SMS (`SmsProvider`), LLM (`LlmClient`, with
  OpenAI-compatible, "needs configuration" and fake implementations) and each
  external provider sit behind an interface selected by environment variables.
- **Browser worker:** `automation/browser` is a separate Playwright + Chromium
  container. It contains a local HTML fixture form and a script that fills
  and submits it. In this MVP the backend uses an in-process sandbox adapter
  for service requests, and the worker container only verifies that Chromium
  launches.
- **Frontend:** Next.js App Router pages for sign-in, onboarding, assistant
  chat, tasks, agenda, approvals, comparison, takeover, notifications,
  account/plans, help, coverage and ops. A web app manifest is included
  for add-to-home-screen. There is no service worker or offline mode.

The full product specification is in
[`docs/iran_native_personal_action_agent_mvp_spec.md`](docs/iran_native_personal_action_agent_mvp_spec.md).
[`docs/implementation_progress.md`](docs/implementation_progress.md) maps each
acceptance scenario to its automated test and lists known limitations.

## Tech stack

| Layer | Technologies |
|---|---|
| Frontend | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS 4, shadcn/ui (Radix), TanStack Query, React Hook Form, Zod, Vazirmatn font |
| Backend | Python 3.13, Django 5.2, Django REST Framework, Pydantic, Celery 5.6 + django-celery-beat, jdatetime, httpx |
| Data | PostgreSQL 17 (pgvector image; extension enabled but not used yet), Redis 8 |
| Automation | Playwright + Chromium (Python) |
| Tooling | Docker Compose, uv, npm, Ruff, ESLint, Prettier, pytest, Vitest |

## Repository layout

```text
yavar/
├── apps/web/              # Next.js frontend (Persian RTL UI)
│   └── src/{app,components,lib}
├── backend/               # Django project
│   ├── config/            # settings (base/development/production), urls, celery
│   └── apps/              # domain apps: accounts, agent, approvals, billing, ...
├── automation/browser/    # Playwright worker + local HTML form fixture
├── docker/                # Dockerfiles and Postgres init script
├── docs/                  # product spec and acceptance-test traceability
├── docker-compose.yml
├── Makefile
└── .env.example
```

## Getting started

### Option A: full stack in Docker (recommended)

Requires Docker with Compose.

```bash
cp .env.example .env
make up          # builds and starts web, backend, celery-worker, celery-beat, browser-worker, postgres, redis
make logs        # follow logs
```

- Web app: http://localhost:3000
- API health check: http://localhost:8000/api/health/
- Django admin: http://localhost:8000/admin/

The backend container runs migrations and seeds the capability registry on
startup. To sign in, enter an Iranian-format mobile number (e.g.
`09120000000`). The console SMS provider prints the code in the backend logs
as `[YAVAR SMS] to=+98… body=…`.

Optional: create a demo user labeled as sandbox with
`docker compose exec backend python manage.py seed_demo`. With the Option B
host setup, use `make seed-demo`.

Stop everything with `make down`.

### Option B: run services on the host

Requires Node.js 22+, Python 3.13 and [uv](https://docs.astral.sh/uv/). The
`.env` file at the repository root is read by Django and points at
`localhost:5433` (Postgres) and `localhost:6379` (Redis).

```bash
cp .env.example .env
make install                          # npm ci, uv sync, Playwright Chromium
docker compose up -d postgres redis   # or provide your own Postgres 17 + pgvector and Redis
make migrate
make seed                             # capability registry and plans
make backend                          # Django on :8000
make web                              # Next.js on :3000 (separate terminal)
make worker                           # Celery worker (separate terminal)
make beat                             # Celery Beat, fires due reminders (separate terminal)
```

## Configuration

All configuration comes from environment variables. Copy `.env.example` to
`.env`. Every value in it is a development placeholder.

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_SETTINGS_MODULE` | Core Django settings |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT` | Database (Compose publishes Postgres on host port 5433) |
| `REDIS_URL` | Celery broker and result backend |
| `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS` | Origins allowed to call the API with credentials |
| `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` | Secure-cookie flags (forced on in production settings) |
| `NEXT_PUBLIC_API_URL` | API base URL used by the web app |
| `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` | Any OpenAI-compatible endpoint. Leave the key empty to run without an LLM |
| `SMS_PROVIDER` | `console` (logs messages). A real gateway is not implemented yet |
| `PROVIDER_MODE`, `PAYMENT_PROVIDER` | `sandbox` (the only implemented mode) |

## Testing and quality

```bash
make test          # frontend (Vitest) + backend (pytest)
make test-web      # Vitest only
make test-backend  # pytest only (needs the Postgres service running)
make lint          # ESLint + tsc typecheck + Ruff (backend and browser worker)
make format        # Prettier + Ruff format
```

The backend suite has tests named after the spec's acceptance scenarios
(AC-01 to AC-46) and quality requirements. These cover approval expiry and
invalidation, double-tap idempotency, cancel-during-send, cross-account
isolation, entitlement restore and prompt-injection handling. It also runs a
100-entry scenario harness: 89 sandbox scenarios run, and 11 live-provider
scenarios are skipped on purpose until real providers exist. The LLM is
replaced by a `FakeLlmClient` in tests, so no network access is needed.

## Project status

Early-stage personal project: two commits, built as an end-to-end MVP of the
product spec in `docs/`. Everything runs locally against sandbox adapters. It
has not been deployed, has no real users, and still needs live provider
integrations, a real SMS gateway and a payment service provider (PSP) before
any public beta.
