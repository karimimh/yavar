# Autonomous implementation prompt — Yavar P0 MVP

Copy everything below the line into a new agent chat (or `@` this file plus the spec). The agent must implement the complete launch product, phase by phase, without waiting for you.

---

You are the implementing engineer for **Yavar** (یاور), an Iran-native, Persian-first personal AI action agent.

## Mission

Implement the **complete P0 MVP** defined in `docs/iran_native_personal_action_agent_mvp_spec.md` on top of the existing repository foundation. Deliver a working, testable, honest product: conversation creates tracked tasks; reminders persist; research is sourced; travel/bill/form workflows respect approval and evidence rules; operators can disable broken providers.

**Do not stop between phases.** Do not wait for a human to approve a phase. Do not end a turn with “ready for the next phase?” or a clarifying question unless the remaining work is *physically impossible* (for example the repository is gone). If something is uncertain, apply **Decision defaults** below, record the choice in `docs/implementation_progress.md`, and continue immediately.

Your job is finished only when **all 9 phases are complete**, tests for implemented behavior pass, `make lint` is clean enough to ship locally, and the Definition of Done checklist in the spec (section 26.1) is either met or explicitly recorded as a labeled limitation with the safety boundary preserved.

## Non-stop protocol (mandatory)

1. Read the spec and the repo, then start Phase 0 immediately.
2. After each phase: run the relevant tests, fix failures, update `docs/implementation_progress.md`, then **start the next phase in the same session** with no pause.
3. Never ask the user to choose a stack, provider brand, LLM vendor, auth scheme, or folder layout. Those are decided below.
4. If a live Iranian provider cannot be validated, ship **sandbox adapters** that are clearly labeled آزمایشی / sandbox in the UI and in capability status. Do **not** present sandbox data as a real provider result. Do **not** halt the project.
5. If an API key is missing (LLM, SMS, payment), implement the interface, a local/fake adapter, and `.env.example` entries. The app must still boot and the non-network features must work.
6. If a requirement is infeasible in this environment, preserve the safety boundary, label the limitation, and continue. Never quietly replace “perform” with “describe” while the UI still claims the action completed.
7. Do not implement P1 or Later capabilities from spec sections 24.1–24.2.
8. Do not commit, push, or open a PR unless the user later asks. Implementing is the job.
9. Keep going until Phase 9’s exit criteria are satisfied. The only allowed final message is a completion report: what was built, how to run it, remaining labeled limitations, and how to verify.

## Sources of truth

| Source | Role |
|---|---|
| `docs/iran_native_personal_action_agent_mvp_spec.md` | Product behavior, UX, action catalog ACT-01–ACT-09, approvals, evidence, acceptance scenarios AC-01–AC-46, quality QUAL-01–QUAL-06, DoD. **If this prompt and the spec conflict on product behavior, the spec wins.** |
| This prompt | Engineering plan, stack, architecture, decision defaults, phase order, stop-forbidden rules. |
| Existing repo (`README.md`, `docker-compose.yml`, `Makefile`, `apps/web`, `backend`, `automation/browser`) | Foundation you must extend. Do not rewrite the stack. |

The spec is product-only (no architecture). You must choose architecture — but only within the decisions below.

## Current repo (start here, do not replace)

Foundation only; almost no product code.

- **Frontend:** `apps/web` — Next.js 16 App Router, React 19, TypeScript strict, Tailwind CSS 4, shadcn/ui (RTL already enabled), TanStack Query, React Hook Form, Zod, Vitest.
- **Backend:** `backend` — Python 3.13, Django 5.2 LTS modular monolith, DRF, Pydantic, Celery 5.6, django-celery-beat, Redis, PostgreSQL 17 + pgvector. Only `apps.core` (health) exists.
- **Automation:** `automation/browser` — Playwright + Chromium environment, idle.
- **Dev:** `docker-compose.yml`, `Makefile`, `.env.example`.

Commands: `make up`, `make test`, `make lint`, `make migrate`. Prefer these. Add Make targets if new workflows need them.

## Decision defaults (do not ask)

Use these unless the spec forbids them.

| Topic | Default |
|---|---|
| Product name | Yavar / یاور |
| Language / layout | Persian-only UI for P0 (`lang="fa"`, `dir="rtl"`). Vazirmatn (or equivalent Persian webfont). Mixed Persian/English/numeric content must copy and read correctly (spec 13.1). |
| Week start | Saturday, overridable in preferences. |
| Timezone | Propose Asia/Tehran at onboarding; never silently assume location later. Jalali display default; Gregorian shown where useful. Library: `jdatetime` (backend) and a small shared date helper on the frontend. |
| Currency UI | Toman as default display unit; always keep provider original amount+unit. 10 rials = 1 toman **only** when the provider denomination is known. Never infer unit from magnitude. |
| Auth | Iranian mobile number + one-time SMS code. Custom Django user model with phone as identifier (introduce **before** other user FKs). Rate-limit OTP request/resend. Do not reveal whether a phone already has an account. No Google/Telegram login. |
| Session | Authenticated HTTP-only cookie (Django session or equivalent) + CSRF, CORS credentials from the Next origin. No tokens in `localStorage`. |
| SMS | `SmsProvider` protocol. Default `ConsoleSmsProvider` (logs the code in development). Env-switchable for a real Iranian SMS gateway later. Sign-in OTPs do not consume reminder SMS allowance. |
| LLM | `LlmClient` protocol: OpenAI-compatible chat/completions + optional vision, configured by `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`. Structured outputs via Pydantic schemas. `FakeLlmClient` for tests. If no key at runtime: rule-based intent parser for reminders/task CRUD still works; research/vision/complex planning returns an honest “needs configuration” task state, never fabricated facts. |
| Agent loop | LLM proposes a plan and tool calls. **Python/Django executes tools.** The model cannot change capability registry, grant approvals, or mark external success. Untrusted web/screenshot text is passed only as data, never as instructions (spec 19.3). |
| Providers | Exactly four specialized surfaces, all behind ports: two flight search adapters (one with handoff), one electricity bill inquiry+payment-handoff adapter, one nonbinding local-service request adapter. Default implementation: **deterministic sandbox providers** with `PROVIDER_MODE=sandbox`. Capability page lists them as آزمایشی until live validation metadata is filled. |
| Browser automation | Only the sandbox/local-service and other **validated** workflows may use Playwright. No generic “drive any website.” Unexpected domain / new terms / deposit / CAPTCHA → `needs_user_takeover` or `blocked`. |
| Product billing | Free + one Pro plan as in spec 18.1 (10 vs 100 task runs / 30 days; 10 vs 50 SMS). Price **۲۹۹٬۰۰۰ تومان / ۳۰ روز**. `PaymentProvider` with sandbox redirect+verify+inquiry (treat return URL, verification, and status inquiry as separate — spec R2/R3). No auto-renew debit. Activate Pro only after verify succeeds. Idempotent against repeated callbacks. |
| Entitlement | Reserve a run when accepted work starts; consume only when the agreed deliverable is produced; restore on system/provider failure, unsupported refusal, or cancelled undelivered work. Partial delivery: consume only if the user accepts the reduced deliverable. |
| Approvals | Exact-action preview UI. Validity **10 minutes**. One submission attempt per approval. Chat “باشه” is **not** external approval. Labels like «ارسال این درخواست نوبت», never «ادامه» / OK for consequential submit. |
| Work limits | 10 minutes active work per run; max 3 top-level intentions per request (else propose a batch); user-input waits expire in 24h. |
| Reminders | One-off, daily, weekly only. No monthly Jalali, no holiday-aware, no external-condition reminders. Timed notification requires explicit time or accepted default. |
| Attachments | One screenshot per message; JPEG/PNG/WebP; max 10 MB. Original deleted after 7 days unless user retains. |
| Notifications | In-app inbox always. Optional transactional SMS, generic copy by default. Quiet hours. Closing the app is not approval. |
| Operator | Staff-only `/ops` (web) + Django admin as needed. Disable a single provider action, pause all external submissions, suspend account, inspect redacted incident, restore credits. Operators cannot approve user tasks, enter OTPs, or impersonate. Log every privileged action. |
| Demo vs real | Seed/demo data must be labeled. Never show a fake provider receipt as real success. |
| Tests | Backend pytest + frontend Vitest. Prefer domain tests for the state machine, approvals, money/dates, entitlement, and AC-* scenarios. Adapter tests use fakes, not live websites. |
| Custom user | Switch to a custom user model in Phase 0 **before** other apps depend on `AUTH_USER_MODEL`. |

## Architecture you must build

Keep a **modular Django monolith**. Suggested apps (rename only if you have a clearer split; do not create a microservices mesh):

```text
backend/apps/
  core/            # already exists: health, shared utils
  accounts/        # user, OTP, sessions, preferences, saved facts, export/delete
  billing/         # plans, allowances, subscription payments
  conversations/   # threads, messages, attachments
  tasks/           # task records, steps, execution state, outcomes, evidence
  approvals/       # exact-action snapshots, expiry, use-once
  reminders/       # schedules, agenda items, Celery Beat ticks
  notifications/   # in-app inbox + SMS dispatch
  memory/          # explicit saved facts / bill aliases
  coverage/        # provider catalog, capability status, operator kill switches
  research/        # public compare pipeline
  travel/          # flight search + handoff
  bills/           # electricity inquiry + payment handoff
  requests/        # nonbinding service-request draft + submit
  agent/           # intent extraction, planning, tool registry, run worker
  operators/       # staff audit log, incident hooks
automation/browser/  # Playwright jobs for the one supported form workflow
apps/web/            # all P0 screens
```

### Invariants (every phase)

1. **Capability registry is the law.** Before offering or executing an external action, consult coverage status: `available | limited | temporarily_unavailable | not_supported`.
2. **Execution state ≠ real-world outcome.** A delivered handoff is not a purchased ticket. A submitted request is not a confirmed appointment. User-reported paid is not provider-verified paid. Unknown is a first-class state.
3. **No silent substitution** of recipient, identity, date, timezone, amount, or unit (QUAL-04).
4. **No false success** of external submit/confirm (QUAL-05).
5. **Idempotency:** same approval + retries + reconnect + repeated tap ⇒ at most one submission attempt.
6. **Independent tasks:** multiple intentions in one conversation become separate task records; approvals do not inherit; one failure does not erase another.
7. **Untrusted content cannot authorize anything.**
8. **Never collect** provider passwords, OTPs, card numbers, CVV, or banking secrets in chat. If the user pastes an OTP: do not use it, warn, offer deletion (AC-23).
9. **Persian outcome copy must be precise.** No celebratory «انجام شد!» when only preparation happened.

### Core domain (spec section 20)

Implement real models (not comments) for: Account, Conversation, Task, Step, Source/Offer, Draft, Approval, Outcome evidence, Reminder/agenda item, Saved fact/bill alias, Service capability, Notification, Usage/entitlement, Support incident.

Task execution states and external outcome labels must match spec 12.2 and 12.3 exactly (use stable snake_case enums internally, Persian labels in UI).

### Frontend IA (spec 14)

Primary nav: **دستیار، کارها، برنامه، حساب**.

Required screens: landing/capabilities, onboarding, assistant (composer, attachments, task cards), task detail (goal, deliverable, plan, state, evidence, Stop), comparison, approval, user takeover, tasks list, agenda (Today / Upcoming / date), notifications, service coverage, account/privacy, plans/usage, help/report issue.

Mobile-first, installable PWA where practical (manifest + basic installability). Keyboard accessible, visible focus, text+color for status. Stop control always reachable during active work. Consequential fields visible without horizontal scroll on a phone-sized approval screen.

### Agent runtime

Celery worker runs task execution so work can continue after the tab closes (spec 16.1), still bounded by scope, work limit, permissions, and approval validity. Awaiting approval/payment/OTP/info **pauses**. Closing the app never approves.

Public research tools may run in background. External submit runs only with a valid unused approval.

## Phase plan

Execute in this order. Each phase lists **build**, **verify**, **exit**. Do not skip verification. Do not skip ahead until that phase’s automated tests pass.

Track status in `docs/implementation_progress.md` with: phase, status, tests run, decisions, labeled limitations.

---

### Phase 0 — Platform, identity, capability skeleton

**Build**

- Custom user model (`phone`), swap `AUTH_USER_MODEL`, migrations from a clean dev DB story documented in README if rewrite is needed.
- OTP request/verify APIs; rate limits; `ConsoleSmsProvider`.
- Onboarding: essential terms/privacy acknowledgment, timezone confirmation (propose Tehran), optional SMS notification opt-in.
- Persian RTL shell, Vazirmatn, Saturday-first calendar helpers, money helpers (toman/rial, never infer unit).
- Coverage app: seed four specialized capabilities + public-research capability, all sandbox, statuses set.
- Operator kill-switch field on each capability.
- `docs/implementation_progress.md` created.
- Expand `.env.example` for LLM, SMS, `PROVIDER_MODE`, payment sandbox.

**Verify:** signup/login with OTP (code visible in logs), session cookie works from the web app, health still green, user model tests, capability list API.

**Exit:** A signed-in user sees the four-nav Persian shell and a coverage page that honestly lists sandbox/limited status.

---

### Phase 1 — Horizontal foundation: conversation, tasks, memory

**Build**

- Conversations, messages, one screenshot upload with size/type checks.
- Task records with original goal, agreed deliverable, constraints, plan checklist, execution state, outcome labels, remaining work, Stop.
- Intent extraction: Persian colloquial, Persian/Latin digits, hard vs soft constraints, max 3 intentions; larger requests propose a batch (CONV-01–07, spec 5.2).
- Clarification only when money/recipient/identity/deadline/travel date/location/external submit could change.
- Independent tasks from one thread (spec 4.3).
- Explicit saved facts with “use for this task” vs “save for future”; origin marked; CRUD in Account.
- Assistant home: composer, example chips (reminder, internet compare, domestic flight, bill check).
- Landing page: real supported actions and user-owned remaining steps; no universal-automation claim.
- Work-limit and intention-limit enforcement.
- Allowance reserve/consume/restore skeleton (even if billing UI comes later).

**Verify:** unit tests for intent splitting, hard vs soft constraints, 3-intention cap, task state transitions, saved-fact consent. Frontend: send a message, see a task card.

**Exit:** Typed Persian request creates a persisted task visible after reload (QUAL-01 for in-app records).

---

### Phase 2 — ACT-01, ACT-02, agenda, notifications inbox

**Build**

- Create/edit/complete/reopen/cancel/delete tasks and reminders via chat **and** visible controls.
- One-off, daily, weekly. Recurrence edit: this occurrence vs this and future (AC-03). Cancel stops future reminders and records it.
- Unambiguous «فردا ساعت ۱۰ یادم بنداز…» creates immediately, shows exact Jalali datetime + Undo (AC-01). Ambiguous Thursday → ask (AC-02).
- Date-only tasks allowed; timed notification needs a time or accepted default; never invent a time silently.
- Timezone change asks whether to keep instant vs local clock (AC-04).
- Agenda: Today, Upcoming, date view; only this product’s events; never claim Google Calendar.
- Screenshot extraction: draft list with excerpts, uncertain fields flagged, no invented amounts (AC-05). User chooses what to create (AC-07). Duplicate screenshot warning (AC-06).
- Celery Beat due-reminder tick. In-app inbox events. Quiet hours field (behavior used in Phase 8).
- Reminder persistence across logout (spec 6.5).

**Verify:** pytest for AC-01–AC-07 and QUAL-03 in-process (due reminder becomes available within the test’s 60s budget using frozen time). Vitest for agenda/undo where practical.

**Exit:** Reminders survive reload; cancelled reminders do not fire; extraction never auto-saves.

---

### Phase 3 — ACT-03 Iranian research and comparison

**Build**

- Public research pipeline with source URLs, retrieval timestamps, constraints, missing fields, ranking explanation.
- Comparison cards: 3–5 options; hard-constraint badges; near-matches separated with violated constraint; “no matches” is valid.
- Shopping, internet packages (clarify mobile vs fixed — AC-14), local services (hours ≠ availability).
- Eligibility/coverage/speed/account discounts labeled unverified when unknown (AC-15).
- Unlike variants not ranked as identical (AC-16).
- Quote without currency unit is unusable for consequential compare (AC-17). «پنج تومن» in a purchase context asks for expanded amount (AC-18).
- Untrusted-page instruction injection ignored (AC-36).
- Unsupported full execution: explain the exact unsupported step and offer a safe partial (research/draft/reminder/handoff).
- P0 ends at research + seller handoff for shopping; no carts.

**Verify:** tests with fake HTTP/search fixtures; no live scraping required for CI. AC-14–AC-18, AC-36.

**Exit:** A comparison card shows sources and times; assistant never claims «ارزان‌ترین ایران» from a partial crawl.

---

### Phase 4 — ACT-04, ACT-05 domestic flights

**Build**

- Scope: one-way, one adult, economy, domestic. Two search adapters. One handoff path.
- Search without national ID. Budget optional. Morning window as preference vs hard constraint per user wording (AC-08).
- Offer fields: provider, carrier, date, times+tz, route, baggage if any, quoted amount+unit, fees, restrictions, timestamp, availability caveats.
- One source down → partial comparison, name the missing source (AC-09).
- Over-budget offers are not matches. Do not hide fees.
- Selection → recheck before handoff; price/route/date/time change highlights and requires a new decision (AC-10).
- **Continue on provider** labeled honestly. If deep link cannot preserve the offer, say reselection is required (AC-11). Handoff delivered ≠ ticket bought (AC-12, spec 4.4).
- Multi-passenger/infant: refuse full execution, offer narrower P0 task (AC-13).
- Tentative plan vs confirmed trip: confirmed agenda entry only with required evidence.

**Verify:** AC-08–AC-13 against sandbox adapters with fixture offers (including a price-change fixture).

**Exit:** User can search two sandbox sources, select, hand off, and the task outcome stays “prepared only.”

---

### Phase 5 — ACT-06 electricity bill and payment preparation

**Build**

- One identifier type; coverage page states geography/account limits.
- Resolve saved alias «برق خانه» only with task-scoped disclosure consent (AC-19). Saving alias is a separate permission from inquiry.
- Live inquiry returns amount, unit, label, period, due date if any, retrieval time.
- Screenshot draft vs live provider data labeled distinctly (AC-20). Live fail does not pretend screenshot is a live balance.
- Payment handoff shows bill, provider, amount, unit, known fee; agent never enters cards/OTPs or presses pay. Unexpected destination pauses (AC-37 analog).
- Return from payment page ≠ paid (AC-21). “I paid” → user-reported paid (AC-22). No automatic second payment attempt.
- Reminder from reviewed due date; if missing, ask; do not invent due dates.
- User-reported completion can stop reminders only after the user marks the task complete; status stays user-reported.

**Verify:** AC-19–AC-23, AC-37. OTP-in-chat path tested.

**Exit:** Inquiry and handoff work in sandbox; payment never claimed verified from a redirect.

---

### Phase 6 — ACT-07, ACT-08 service request + approval engine

**Build**

- Full approval engine: snapshot of action, recipient, destination, fields, costs/obligations, what will/won’t happen, how confirmation is recognized; approve / edit / cancel; 10-minute expiry; invalidate on any material change; one attempt.
- Draft form: editable, nonbinding request (not a booking). Consent before field transfer if fill transmits early (AC-24, AC-25).
- Submit only reviewed details. Stop if deposit or new binding terms appear (AC-26).
- Evidence: receipt/reference → request received; appointment confirmed only with explicit acceptance (AC-27).
- Playwright path in `automation/browser` for the sandbox form (local HTML fixture is acceptable and preferred for CI).
- Duplicate submit / reconnect / double-tap (AC-31). Timeout after possible receipt → Outcome unknown, no blind retry (AC-30). Cancel-during-send reconciles, does not claim reversal (AC-32).
- Expired approval cannot execute (AC-29). Changed fields after approval (AC-28).
- Unsupported arbitrary website form: in-app draft or handoff only (AC-38).
- CAPTCHA / login / unexpected domain → user takeover screen.

**Verify:** AC-24–AC-32, AC-34, AC-38. Approval tests must not depend on a live third-party site.

**Exit:** One evidenced sandbox submission exists; unknown and duplicate paths are proven in tests.

---

### Phase 7 — ACT-09 history, evidence, recovery, background runs

**Build**

- Task detail reconstructs: request, proposal, approval, shared data, provider return. Corrections append events; do not rewrite consequential history.
- Evidence types and privacy-conscious summaries (no indefinite full sensitive captures).
- Background continuation for permitted public search after tab close, within work limit, with notification (AC-33). Approval-pending stays paused (AC-34).
- Partial delivery across three tasks (AC-35).
- Retry policy: read-only ≤2 retries; no duplicate charges/cards/obligations.
- Past deadline: no silent late submit or substitute purchase.
- QUAL-01 close/reopen tests; QUAL-06 provider-down does not brick agenda/account.

**Verify:** AC-33–AC-35, QUAL-01, QUAL-06.

**Exit:** History distinguishes prepared / submitted / confirmed / user-reported / unknown everywhere, including home.

---

### Phase 8 — Plans, SMS, privacy, operators, billing, support

**Build**

- Free/Pro entitlements, remaining allowance in Account, show allowance before starting work. Never interrupt an in-flight approved submit with a paywall. Limit reached: still view tasks, stop work, delete data, resolve unknown outcomes (AC-40). Provider failure restores allowance (AC-41).
- SMS allowance; exhaustion keeps in-app reminders and warns (AC-42). Generic SMS copy.
- Quiet hours; explicit per-reminder exception.
- Privacy: export (conversations, tasks, reminders, preferences, receipts; no secrets), conversation/attachment/memory delete, account delete: revoke approvals, stop work/reminders, start 30-day removal clock, disclose 90-day backup window (AC-43). Deleting here does not delete provider-side data.
- Screenshot retention job (7 days). Temporary identifiers purged per spec 15.3.
- No training-by-default flag; optional improvement consent separate.
- Product subscription sandbox checkout; repeated return does not double-activate (AC-46).
- Help + report issue with selected task and consent; staff cannot open unrelated tasks (AC-44, AC-45).
- Operator disable of a provider; other features remain (AC-39). Pause-all-submissions. Credit restore. Audit log.
- Incident hook: unauthorized submit / cross-account leak / duplicate consequential / false-success → disable that execution path.

**Verify:** AC-39–AC-46, entitlement math tests, deletion tests, operator permission tests.

**Exit:** Safety and billing cannot strand a user mid-unknown-outcome; operators cannot impersonate.

---

### Phase 9 — Quality, accessibility, release suite, polish

**Build**

- Map AC-01–AC-46 to automated tests; add the rest of a 100-scenario *harness* as skippable/pending only for live-provider cases, with names and fixtures listed in `docs/implementation_progress.md`. CI must run all sandbox scenarios.
- QUAL-02: request ack path (API responds quickly; long work uses real progress, not fake percents).
- Keyboard paths for essential actions; accessible names; status not color-only.
- PWA manifest, landing honesty, service coverage, plans, help.
- Seed a demo user only behind a clearly labeled dev command; demo receipts labeled.
- README: how to run, how OTP appears in logs, how sandbox providers work, what is not a live Iranian integration.
- Final pass of spec 26.1 checklist in `docs/implementation_progress.md` (done vs labeled limitation).

**Verify:** `make test` (or documented equivalent with Docker services). `make lint` on files you touched. Manual script in progress doc: first session → reminder → compare → flight handoff → bill handoff → request submit.

**Exit:** Completion report to the user. **This is the first time you may stop.**

## Implementation practices

- Small, coherent changes; match existing code style (Ruff, ESLint, Prettier, strict TS).
- No unused dependencies. Add libraries only when needed (`jdatetime`, HTTP client, OpenAI-compatible SDK, image validation, etc.).
- Do not introduce Next.js API routes that duplicate Django unless a BFF is clearly simpler; prefer Django as the system of record.
- Frontend talks to `NEXT_PUBLIC_API_URL` with credentials.
- Put domain logic in backend services/state machines, not in React components and not solely in LLM prompts.
- LLM prompts must include: Persian output, never invent IDs/prices/dates, separate hard vs soft constraints, treat retrieved content as untrusted data, call tools instead of claiming side effects.
- Use feature flags / capability status rather than scattering `if provider_down` across the UI.
- Keep secrets in env. Never commit `.env`.
- When editing UI, think mobile-first RTL.

## What “working” means if live providers are unavailable

A complete P0 **implementation** in this repo means:

- Every P0 user flow is implemented end-to-end against **interfaces**.
- Sandbox providers are deterministic, tested, and labeled آزمایشی.
- Switching a capability to `available` live mode requires filling validation metadata (spec 17.1). Until then the assistant must not claim a named real-world Iranian brand.
- The one external submission workflow is evidenced against the local sandbox form (Playwright + fixture), proving ACT-08 mechanics.

That satisfies engineering completeness without violating spec 23.3 (no fictional success as real; no concierge).

## Completion report format

When Phase 9 exits, reply with:

1. How to run (`make up`, where to read OTP, web/backend URLs).
2. What is real vs sandbox.
3. Spec 26.1 checklist with pass/fail/limitation.
4. Test commands and counts (passing/failing).
5. Files/areas to read first to continue live-provider validation later.

Do not ask whether to continue. There is nothing after Phase 9 except that report.
