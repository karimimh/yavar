# Implementation progress — Yavar P0 MVP

Last updated: 2026-09-17

## Decision defaults applied

- Persian-only UI (`lang=fa`, `dir=rtl`), Vazirmatn, Saturday-first week.
- Timezone proposed Asia/Tehran at onboarding; Jalali display; `jdatetime` + frontend helper.
- Toman display; rial conversion only when denomination is known.
- Auth: Iranian mobile + OTP; HTTP-only session cookie; `ConsoleSmsProvider`.
- LLM: OpenAI-compatible env; `FakeLlmClient` in tests; rule-based parser when no key.
- Four specialized sandbox surfaces + public research; `PROVIDER_MODE=sandbox`.
- Pro plan ۲۹۹٬۰۰۰ تومان / ۳۰ روز; sandbox payment return ≠ verify ≠ inquiry.
- Custom user model `accounts.User` (phone). Existing Docker Postgres volumes from the
  empty foundation must be recreated once (`docker volume rm yavar_postgres_data`).

## Phase status

| Phase | Status | Notes |
|---|---|---|
| 0 Platform, identity, coverage | complete | Custom user, OTP, CSRF session, capability registry, coverage page |
| 1 Conversation, tasks, memory | complete | Send message, independent tasks, saved facts, execution ≠ outcome |
| 2 ACT-01/02 reminders, agenda | complete | Jalali, timezone, screenshot review, inbox, QUAL-03 |
| 3 ACT-03 research | complete | Internet clarify, sources, injection ignored |
| 4 ACT-04/05 domestic flights | complete | Two sandbox sources, honest handoff, budget/morning |
| 5 ACT-06 electricity bill | complete | Consent, inquiry, stop before payment, user-reported paid |
| 6 ACT-07/08 service request + approvals | complete | Draft, 10-min approval, one attempt, Playwright fixture |
| 7 ACT-09 history, evidence, recovery | complete | Background research, cancel, unknown, QUAL-01/06 |
| 8 Plans, SMS, privacy, operators | complete | Entitlements, export/delete, ops disable, sandbox checkout |
| 9 Quality, harness, polish | complete | AC map, 100-name harness, README, lint |

## Labeled limitations

- No live Iranian travel / bill / form / SMS provider. Sandbox adapters only; results labeled آزمایشی.
- Screenshot extraction requires LLM vision; without a key, drafts stay empty and unsaved.
- Playwright submits the **local HTML fixture**, not a production website.
- Product billing is sandbox; return ≠ verify ≠ inquiry; not a real PSP.
- Existing Postgres volumes created before `AUTH_USER_MODEL` need a one-time reset.
- Public-beta live-provider gate (spec 17.1 validation metadata) is not claimed.

## AC → automated tests

| AC | File | Test |
|---|---|---|
| AC-01 | `apps/reminders/tests/test_ac_reminders.py` | `test_ac01_unambiguous_reminder` |
| AC-02 | same | `test_ac02_ambiguous_thursday_asks` |
| AC-03 | same | `test_ac03_recurrence_this_vs_future` |
| AC-04 | same | `test_ac04_timezone_change_asks` |
| AC-05 | same | `test_ac05_blurred_amount_not_invented` |
| AC-06 | `apps/conversations/tests/test_send.py` | `test_ac06_duplicate_screenshot_warns` |
| AC-07 | `apps/reminders/tests/test_ac_reminders.py` | `test_ac07_extraction_not_auto_saved` |
| AC-08 | `apps/travel/tests/test_ac_travel.py` | `test_ac08_hard_budget_morning` |
| AC-09 | same | `test_ac09_partial_source` |
| AC-10 | same | `test_ac10_price_change_requires_new_decision` |
| AC-11 / AC-12 | same | `test_ac11_ac12_handoff_honest` |
| AC-13 | same | `test_ac13_multi_passenger_refused` |
| AC-14 | `apps/research/tests/test_ac_research.py` | `test_ac14_internet_clarify` |
| AC-15 | same | `test_ac15_unverified_coverage` |
| AC-16 | same | `test_ac16_unlike_variants_not_identical` |
| AC-17 | same | `test_ac17_missing_unit_unusable` |
| AC-18 | same | `test_ac18_five_toman_asks` |
| AC-19 | `apps/bills/tests/test_ac_bills.py` | `test_ac19_alias_requires_consent`, `test_ac19_consent_then_inquire` |
| AC-20 | same | `test_ac20_live_fail_does_not_claim_screenshot` |
| AC-21 | same | `test_ac21_return_not_paid` |
| AC-22 | same | `test_ac22_user_reported_paid` |
| AC-23 | same | `test_ac23_otp_in_chat` |
| AC-24 | `apps/approvals/tests/test_ac_approvals.py` | `test_ac24_draft_preview` |
| AC-25 | same | `test_ac25_fill_consent_required` |
| AC-26 | same | `test_ac26_deposit_stops` |
| AC-27 | same | `test_ac27_ack_not_appointment` |
| AC-28 | same | `test_ac28_field_change_invalidates` |
| AC-29 | same | `test_ac29_expired_cannot_execute` |
| AC-30 | same | `test_ac30_timeout_unknown_no_retry` |
| AC-31 | same | `test_ac31_double_tap` |
| AC-32 | same | `test_ac32_cancel_during_send` |
| AC-33 | `apps/operators/tests/test_ac_ops_billing.py` | `test_ac33_background_research` |
| AC-34 | `apps/approvals/tests/test_ac_approvals.py` | `test_ac34_close_app_not_approval` |
| AC-35 | `apps/operators/tests/test_ac_ops_billing.py` | `test_ac35_partial_three_tasks` |
| AC-36 | `apps/research/tests/test_ac_research.py` | `test_ac36_injection_ignored` |
| AC-37 | `apps/bills/tests/test_ac_bills.py` | `test_ac37_unexpected_payment_domain` |
| AC-38 | `apps/approvals/tests/test_ac_approvals.py` | `test_ac38_arbitrary_form` |
| AC-39 | `apps/operators/tests/test_ac_ops_billing.py` | `test_ac39_operator_disable` |
| AC-40 | same | `test_ac40_limit_unknown_recovery` |
| AC-41 | same | `test_ac41_provider_failure_restores` |
| AC-42 | same | `test_ac42_sms_exhausted_keeps_inbox` |
| AC-43 | same | `test_ac43_delete_account` |
| AC-44 | same | `test_ac44_operator_cannot_open_unrelated` |
| AC-45 | same | `test_ac45_no_cross_account` |
| AC-46 | same | `test_ac46_repeat_payment_return` |
| QUAL-01 | `apps/operators/tests/test_ac_ops_billing.py` | `test_qual01_task_survives` |
| QUAL-02 | `apps/conversations/tests/test_send.py` | `test_qual02_ack_fast` |
| QUAL-03 | `apps/reminders/tests/test_ac_reminders.py` | `test_qual03_due_reminder_within_60s` |
| QUAL-06 | `apps/operators/tests/test_ac_ops_billing.py` | `test_qual06_provider_down_agenda_ok` |

## 100-scenario harness

CI runs all sandbox names. Live names are skipped until spec 17.1 validation metadata exists.

### Sandbox nominal (`apps/agent/tests/test_harness.py`) — 19

`s01_reminder_tomorrow`, `s02_reminder_today_time`, `s03_daily`, `s04_weekly`,
`s05_flight_thr_syz`, `s06_flight_budget`, `s07_flight_morning`, `s08_shop_compare`,
`s09_internet_mobile`, `s10_internet_fixed`, `s11_local_hours`, `s12_service_request`,
`s13_personal`, `s14_unsupported_hotel`, `s15_two_intents`, `s16_bill_inquiry`,
`s17_flight_tabriz`, `s18_quiet_hours`, `s19_takeover_request`

### Provider-surface sandbox (`apps/agent/tests/test_release_harness.py`) — 70

- `flight_0` … `flight_19` — Tehran/Shiraz/Mashhad/Isfahan/Tabriz edges
- `bill_msg_0` … `bill_msg_19` — electricity inquiry with distinct bill IDs
- `form_0` … `form_9` — oil-change request hours 8–17
- `research_0` … `research_19` — headphones / mobile internet / fiber / local hours

### Live-provider pending (skipped) — 11

From `test_harness.py`:

- `live_flight_alpha_real_brand`
- `live_flight_beta_real_brand`
- `live_electricity_real_provider`
- `live_service_form_real_shop`
- `live_sms_gateway_deliverability`

From `test_release_harness.py` (spec 17.1 fixtures):

- `live_alpha_search_prod`
- `live_alpha_handoff_prod`
- `live_beta_search_prod`
- `live_bill_inquiry_prod`
- `live_bill_pay_page_prod`
- `live_form_submit_prod`

**Total named harness entries: 19 + 70 + 11 = 100.**

## Manual script

1. `cp .env.example .env` then `make up` → open http://localhost:3000
2. Sign in with an Iranian mobile. OTP appears in backend logs as `[YAVAR SMS] … YAVAR OTP 123456`.
3. Onboarding: accept proposed Asia/Tehran timezone.
4. Assistant chips / prompts:
   - Reminder → appears on agenda; Jalali date visible
   - Compare internet → must clarify همراه vs ثابت; sources labeled آزمایشی
   - Flight Tehran→Shiraz → two sandbox sources + honest handoff (not a ticket)
   - Electricity bill → consent, inquiry, stop before payment
   - Oil-change request → preview, approve within 10 minutes, submit to local fixture
5. Confirm outcomes stay prepared / request received / user-reported / unknown — never fake paid/ticket.
6. Account: remaining allowance, export, delete copy (30-day removal, 90-day backup).
7. Operator (seeded demo if used): disable a provider; reminders still work.

Demo user (labeled sandbox): `make seed-demo`

## Spec 26.1 checklist

- [x] Sign in without external accounts — **pass**
- [x] Persian conversation → persistent tasks — **pass**
- [x] Reminders with Jalali/timezone — **pass**
- [x] Screenshot drafts reviewed before create — **pass** (vision empty without LLM key; still not auto-saved)
- [x] Comparisons with sources — **pass** (sandbox sources, labeled آزمایشی)
- [x] Two sandbox flight sources + honest handoff — **pass** (live brands: **limitation**)
- [x] Electricity inquiry; stop before payment — **pass** (sandbox inquiry, not a live utility)
- [x] One evidenced sandbox request submit — **pass** (Playwright + local HTML fixture)
- [x] Capability registry + exact approval — **pass**
- [x] Outcome labels distinguishable — **pass**
- [x] Tasks survive reload (DB) — **pass**
- [x] Cancel / expiry / unknown tested — **pass**
- [x] Privacy export/delete/support access — **pass**
- [x] Limits + sandbox subscription — **pass**
- [x] Operator disable without killing reminders — **pass**
- [ ] Public-beta live-provider gate — **labeled limitation** (spec 17.1 metadata not filled; no fictional live success)
