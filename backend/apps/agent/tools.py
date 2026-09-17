"""Tool implementations executed by Django, never by the model claiming side effects."""

from __future__ import annotations

from django.utils import timezone

from apps.agent.llm import IntentItem, get_llm_client
from apps.approvals.services import create_approval
from apps.bills import adapters as bill_adapters
from apps.core.dates import resolve_relative_date
from apps.core.enums import EvidenceType, ExecutionState, ExternalOutcome, Recurrence
from apps.core.money import UnusableQuoteError
from apps.coverage.services import require_executable
from apps.memory.models import SavedFact
from apps.reminders.services import create_reminder, display_when
from apps.requests import adapters as request_adapters
from apps.research import adapters as research_adapters
from apps.tasks.models import Draft, Offer, Task
from apps.tasks.state import add_evidence, append_event, set_outcome, transition
from apps.travel import adapters as travel_adapters


def _consume(task: Task, reason: str) -> None:
    from apps.billing.services import consume_run

    if task.allowance_reserved and not task.allowance_consumed:
        consume_run(task.user, task_id=task.id, reason=reason)
        task.allowance_consumed = True
        task.save(update_fields=["allowance_consumed"])


def _restore(task: Task, reason: str) -> None:
    from apps.billing.services import restore_run

    if task.allowance_reserved and not task.allowance_consumed:
        restore_run(task.user, task_id=task.id, reason=reason)
        task.allowance_reserved = False
        task.save(update_fields=["allowance_reserved"])


def run_reminder(task: Task, item: IntentItem | None, *, now=None) -> Task:
    text = (item.original if item else task.original_wording) or task.original_goal
    resolved = resolve_relative_date(text, timezone=task.user.timezone, now=now)
    payload = item.payload if item else task.payload
    if resolved and resolved.ambiguous:
        task.payload["clarification"] = resolved.clarification
        task.save(update_fields=["payload"])
        return transition(
            task,
            ExecutionState.NEEDS_INFORMATION,
            activity_fa=resolved.clarification or "تاریخ مبهم است",
        )
    if resolved is None:
        from datetime import datetime, timedelta

        from apps.core.dates import now_in, parse_clock, tzinfo_of

        clock = parse_clock(text)
        recurrence = payload.get("recurrence", Recurrence.ONE_OFF)
        if clock and recurrence in {Recurrence.DAILY, Recurrence.WEEKLY}:
            current = now.astimezone(tzinfo_of(task.user.timezone)) if now else now_in(task.user.timezone)
            instant = datetime.combine(current.date(), clock, tzinfo=tzinfo_of(task.user.timezone))
            if instant <= current:
                instant = instant + timedelta(days=1)
            from apps.core.dates import WEEKDAY_FA, ResolvedDateTime, to_jalali_date

            resolved = ResolvedDateTime(
                instant=instant,
                timezone=task.user.timezone,
                jalali_date=to_jalali_date(instant.date()),
                gregorian_date=instant.date().isoformat(),
                time_display=clock.strftime("%H:%M"),
                weekday_fa=WEEKDAY_FA[instant.weekday()],
            )
        else:
            return transition(task, ExecutionState.NEEDS_INFORMATION, activity_fa="تاریخ را مشخص کنید.")
    if payload.get("date_only") and resolved.time_display is None:
        if not task.user.default_reminder_time:
            return transition(
                task,
                ExecutionState.NEEDS_INFORMATION,
                activity_fa="برای نوتیفیکیشن زمان‌دار باید ساعت را بگویید یا پیش‌فرض ذخیره کنید. ساعت اختراع نمی‌شود.",
            )
        from datetime import datetime

        from apps.core.dates import tzinfo_of

        resolved_instant = datetime.combine(
            resolved.instant.date(), task.user.default_reminder_time, tzinfo=tzinfo_of(task.user.timezone)
        )
    else:
        if resolved.time_display is None and not payload.get("date_only"):
            # Unambiguous «فردا ساعت ۱۰» always has time. If missing, ask.
            return transition(
                task,
                ExecutionState.NEEDS_INFORMATION,
                activity_fa="ساعت یادآور مشخص نیست.",
            )
        resolved_instant = resolved.instant

    recurrence = payload.get("recurrence", Recurrence.ONE_OFF)
    reminder = create_reminder(
        user=task.user,
        title=task.title,
        due_at=resolved_instant,
        timezone_name=task.user.timezone,
        recurrence=recurrence,
        task=task,
        details=text,
    )
    task.payload["reminder_id"] = reminder.id
    task.payload["display_fa"] = display_when(reminder)
    task.payload["undo"] = True
    task.save(update_fields=["payload"])
    task.current_activity_fa = f"یادآور ساخته شد: {display_when(reminder)}"
    task.save(update_fields=["current_activity_fa"])
    return task


def run_research(task: Task, item: IntentItem | None) -> Task:
    ok, info = require_executable("public_research")
    if not ok:
        _restore(task, "capability_blocked")
        return transition(task, ExecutionState.BLOCKED, activity_fa=info.get("reason_fa") or info["label_fa"])
    payload = item.payload if item else task.payload
    topic = payload.get("topic", "shopping")
    internet_kind = payload.get("internet_kind")
    if item and item.needs_clarification == "mobile_vs_fixed" and not internet_kind:
        return transition(
            task,
            ExecutionState.NEEDS_INFORMATION,
            activity_fa="بستهٔ همراه مدنظرتان است یا اینترنت ثابت؟",
        )
    if item and item.needs_clarification == "expand_toman_amount":
        return transition(
            task,
            ExecutionState.NEEDS_INFORMATION,
            activity_fa="منظور از مبلغ کوتاه با «تومن» چیست؟ مقدار کامل و واحد را بنویسید.",
        )
    result = research_adapters.compare(
        topic=topic,
        constraints=task.constraints,
        internet_kind=internet_kind,
    )
    if result.get("needs_clarification"):
        return transition(task, ExecutionState.NEEDS_INFORMATION, activity_fa=result["message_fa"])
    # Untrusted content cannot authorize anything.
    if result.get("untrusted_excerpt_example"):
        append_event(
            task,
            "untrusted_ignored",
            "دستورهای داخل صفحه به‌عنوان مجوز نادیده گرفته شد.",
        )
    Offer.objects.filter(task=task).delete()
    for opt in result.get("options", []):
        try:
            if opt.get("amount") and opt.get("unit"):
                research_adapters.validate_quote(opt)
            amount = opt.get("amount")
            unit = opt.get("unit") or ""
        except UnusableQuoteError:
            amount, unit = None, ""
            opt = {**opt, "unusable": True}
        Offer.objects.create(
            task=task,
            source_slug="public_research",
            provider_name_fa=opt.get("provider", ""),
            title=opt.get("title", ""),
            attributes=opt.get("attributes") or {},
            amount=amount or None,
            unit=unit,
            fees=opt.get("fees") or [],
            source_url=opt.get("source_url", ""),
            retrieved_at=timezone.now(),
            is_match=not opt.get("unusable"),
            unverified_fields=opt.get("unverified") or [],
            sandbox=True,
        )
    for opt in result.get("unusable_quotes", []):
        Offer.objects.create(
            task=task,
            source_slug="public_research",
            provider_name_fa=opt.get("provider", ""),
            title=opt.get("title", ""),
            attributes=opt.get("attributes") or {},
            source_url=opt.get("source_url", ""),
            retrieved_at=timezone.now(),
            is_match=False,
            violated_constraint="واحد پول نامشخص",
            sandbox=True,
        )
    task.payload["comparison"] = result
    task.save(update_fields=["payload"])
    add_evidence(
        task,
        evidence_type=EvidenceType.SOURCE_PAGE,
        summary_fa="مقایسه از منابع آزمایشی با زمان بازیابی ثبت شد.",
        proves="comparison_completed",
        origin="system",
        data={"sources": result.get("sources_checked")},
    )
    set_outcome(task, ExternalOutcome.PREPARED_ONLY, remaining="خرید/سبد خرید پشتیبانی نمی‌شود.")
    _consume(task, "comparison")
    return transition(task, ExecutionState.DELIVERED, activity_fa="مقایسه آماده است (آزمایشی)")


def run_travel_search(task: Task, item: IntentItem | None) -> Task:
    if item and item.needs_clarification == "p0_one_adult_only":
        task.agreed_deliverable = "پیشنهاد کار باریک‌تر: یک بزرگسال، یک‌طرفه، اکونومی"
        task.payload["unsupported_step"] = item.payload.get("unsupported_step")
        task.save()
        set_outcome(task, ExternalOutcome.NOT_SUBMITTED)
        return transition(
            task,
            ExecutionState.BLOCKED,
            activity_fa="چند مسافر/نوزاد در P0 اجرا نمی‌شود. می‌توانید جستجوی یک بزرگسال را بخواهید.",
        )
    ok_a, info_a = require_executable("flight_search_alpha")
    ok_b, info_b = require_executable("flight_search_beta")
    sources = []
    if ok_a:
        sources.append("flight_search_alpha")
    if ok_b:
        sources.append("flight_search_beta")
    if not sources:
        _restore(task, "provider_unavailable")
        return transition(task, ExecutionState.BLOCKED, activity_fa="جستجوی پرواز موقتاً در دسترس نیست.")
    payload = item.payload if item else task.payload
    hard = (item.hard_constraints if item else task.constraints.get("hard")) or {}
    soft = (item.soft_preferences if item else task.constraints.get("soft")) or {}
    # Morning-only as hard when so marked
    result = travel_adapters.search(
        origin=payload.get("origin", "تهران"),
        destination=payload.get("destination", "شیراز"),
        hard=hard,
        soft=soft,
        sources=sources,
    )
    Offer.objects.filter(task=task).delete()
    for row in result["matches"] + result["near_matches"]:
        Offer.objects.create(
            task=task,
            source_slug=row["source_slug"],
            provider_name_fa=row["provider_name_fa"],
            title=f"{row.get('carrier')} {row.get('depart_time')}",
            attributes=row,
            amount=row.get("amount") or None,
            unit=row.get("unit") or "",
            fees=row.get("fees") or [],
            source_url=row.get("handoff_url", ""),
            retrieved_at=timezone.now(),
            is_match=row.get("is_match", True),
            violated_constraint=row.get("violated_constraint", ""),
            sandbox=True,
            handoff_url=row.get("handoff_url", ""),
            preserves_offer=row.get("preserves_offer", False),
        )
    task.payload["search"] = result
    task.save(update_fields=["payload"])
    if result["partial"]:
        names = "، ".join(m["name_fa"] for m in result["missing_sources"])
        activity = f"مقایسه ناقص؛ منبع در دسترس نیست: {names}"
    else:
        activity = "نتایج جستجوی آزمایشی آماده است"
    add_evidence(
        task,
        evidence_type=EvidenceType.SOURCE_PAGE,
        summary_fa=activity,
        proves="comparison_completed",
        origin="system",
    )
    set_outcome(task, ExternalOutcome.PREPARED_ONLY, remaining="خرید بلیط با کاربر روی سایت ارائه‌دهنده است.")
    _consume(task, "travel_search")
    return transition(task, ExecutionState.DELIVERED, activity_fa=activity)


def run_bill_inquiry(task: Task, item: IntentItem | None) -> Task:
    ok, info = require_executable("electricity_bill")
    if not ok:
        _restore(task, "capability_blocked")
        return transition(task, ExecutionState.BLOCKED, activity_fa=info["label_fa"])
    payload = item.payload if item else task.payload
    alias = payload.get("alias")
    if alias:
        fact = SavedFact.objects.filter(user=task.user, kind="bill_alias", label=alias).first()
        if fact and not payload.get("disclosure_consent"):
            task.payload["pending_alias"] = alias
            task.payload["pending_value_masked"] = _mask(fact.value)
            task.save(update_fields=["payload"])
            return transition(
                task,
                ExecutionState.NEEDS_INFORMATION,
                activity_fa=f"برای استعلام، شناسهٔ «{alias}» با {info['name_fa']} به اشتراک گذاشته می‌شود. رضایت این کار را تأیید کنید. ذخیرهٔ دائمی جداست.",
            )
        if not fact:
            return transition(task, ExecutionState.NEEDS_INFORMATION, activity_fa="نام مستعار قبض یافت نشد.")
        bill_id = fact.value
    else:
        bill_id = payload.get("bill_id")
        if not bill_id:
            return transition(task, ExecutionState.NEEDS_INFORMATION, activity_fa="شناسهٔ قبض را وارد کنید.")
        if not payload.get("disclosure_consent"):
            return transition(
                task,
                ExecutionState.NEEDS_INFORMATION,
                activity_fa="شناسه برای استعلام با ارائه‌دهندهٔ آزمایشی به اشتراک گذاشته می‌شود. تأیید می‌کنید؟",
            )
    live = bill_adapters.inquire(bill_id)
    if not live.get("ok"):
        task.payload["live_failed"] = True
        task.save(update_fields=["payload"])
        set_outcome(task, ExternalOutcome.NOT_SUBMITTED)
        _restore(task, "provider_failure")
        return transition(
            task,
            ExecutionState.FAILED,
            activity_fa="استعلام زنده ناموفق بود. دادهٔ تصویر جایگزین موجودی زنده نیست.",
            error_fa=live.get("error_fa", ""),
        )
    task.payload["live_bill"] = live
    task.payload["data_origin"] = "checked_with_provider"
    task.save(update_fields=["payload"])
    add_evidence(
        task,
        evidence_type=EvidenceType.LIVE_PROVIDER,
        summary_fa=f"استعلام آزمایشی: {live['amount']} {live['unit']}",
        proves="live_inquiry",
        origin="provider",
        data={"retrieved_at": live["retrieved_at"], "sandbox": True},
    )
    set_outcome(task, ExternalOutcome.PREPARED_ONLY, remaining="پرداخت انجام نشده و تأیید نشده است.")
    _consume(task, "bill_inquiry")
    return transition(task, ExecutionState.DELIVERED, activity_fa="استعلام آزمایشی آماده است")


def run_service_draft(task: Task, item: IntentItem | None) -> Task:
    ok, info = require_executable("local_service_request")
    if not ok:
        _restore(task, "capability_blocked")
        return transition(task, ExecutionState.BLOCKED, activity_fa=info["label_fa"])
    form = request_adapters.inspect_form()
    if form.get("needs_user_takeover"):
        task.payload["takeover"] = form
        task.save(update_fields=["payload"])
        set_outcome(task, ExternalOutcome.NOT_SUBMITTED)
        return transition(task, ExecutionState.NEEDS_USER_TAKEOVER, activity_fa="نیاز به ادامه توسط شما (کپچا/دامنه)")
    if form.get("blocked"):
        set_outcome(task, ExternalOutcome.NOT_SUBMITTED)
        return transition(task, ExecutionState.BLOCKED, activity_fa=form["message_fa"])
    fields = {
        "name": task.user.preferred_name or "",
        "phone": task.user.phone_original or task.user.phone,
        "area": task.user.city or "",
        "preferred_slot": (item.original if item else task.original_goal),
        "note": "",
        "nonbinding": True,
    }
    Draft.objects.create(
        task=task,
        kind="service_request",
        fields=fields,
        recipient_fa="تعویض روغن سندباکس",
        destination=form["destination"],
        nonbinding=True,
    )
    task.payload["form"] = form
    task.payload["needs_fill_consent"] = form.get("may_transmit_on_fill", False)
    task.save(update_fields=["payload"])
    create_approval(
        task=task,
        action_name="submit_service_request",
        action_label_fa="ارسال این درخواست نوبت",
        recipient_fa="تعویض روغن سندباکس",
        destination=form["destination"],
        fields_snapshot=fields,
        costs_fa="بدون پیش‌پرداخت و بدون تعهد مالی در این جریان آزمایشی.",
        will_happen_fa="درخواست غیرالزام‌آور برای نوبت ارسال می‌شود.",
        will_not_happen_fa="نوبت قطعی نمی‌شود؛ پرداخت یا قرارداد انجام نمی‌شود.",
        confirmation_how_fa="رسید/کد مرجع سندباکس یعنی درخواست دریافت شده، نه تأیید نوبت.",
    )
    return task


def run_unsupported(task: Task, item: IntentItem | None) -> Task:
    payload = item.payload if item else task.payload
    step = payload.get("unsupported_step") or "این گام خارج از محدودهٔ اجراست."
    partial = payload.get("safe_partial") or "پژوهش، پیش‌نویس، یادآور یا تحویل امن"
    task.remaining_work = partial
    task.save(update_fields=["remaining_work"])
    set_outcome(task, ExternalOutcome.NOT_SUBMITTED)
    _restore(task, "unsupported_refusal")
    return transition(
        task,
        ExecutionState.BLOCKED,
        activity_fa=f"{step} انجام نمی‌شود. می‌توانم {partial} را انجام بدهم.",
    )


def run_extraction(task: Task) -> Task:
    client = get_llm_client()
    result = client.vision_extract(
        "تعهدات را استخراج کن. مبلغ ناخوانا را اختراع نکن.",
        b"",
    )
    if result.get("error") == "needs_configuration" and "items" not in result:
        # Tests inject FakeLlmClient. Without LLM, do not invent amounts.
        task.payload["extraction_draft"] = {
            "items": [],
            "message_fa": "استخراج تصویر بدون مدل پیکربندی‌شده ممکن نیست. هیچ یادآوری ذخیره نشد.",
        }
        task.save(update_fields=["payload"])
        return transition(task, ExecutionState.NEEDS_INFORMATION, activity_fa="پیش‌نویس استخراج خالی است؛ چیزی ذخیره نشد.")
    items = result.get("items") or []
    for it in items:
        if it.get("amount_uncertain"):
            it["amount"] = None
            it["flag_fa"] = "مبلغ ناخواناست و حدس زده نشد."
    task.payload["extraction_draft"] = {"items": items, "saved": False}
    task.save(update_fields=["payload"])
    set_outcome(task, ExternalOutcome.NOT_SUBMITTED)
    return transition(
        task,
        ExecutionState.NEEDS_INFORMATION,
        activity_fa="موارد استخراج‌شده پیش‌نویس هستند؛ تا تأیید شما ذخیره نمی‌شوند.",
    )


def _mask(value: str) -> str:
    if len(value) <= 4:
        return "***"
    return value[:2] + "****" + value[-2:]
