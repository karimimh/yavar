from __future__ import annotations

from datetime import datetime, timedelta

from django.utils import timezone

from apps.accounts.models import User
from apps.core.dates import format_jalali_fa, shift_keep_instant, shift_keep_local_clock, tzinfo_of
from apps.core.enums import EvidenceType, ExecutionState, Recurrence
from apps.core.persian import to_persian_digits
from apps.reminders.models import Reminder, ReminderOccurrenceEdit
from apps.tasks.models import Task
from apps.tasks.state import add_evidence, append_event, set_outcome, transition


def create_reminder(
    *,
    user: User,
    title: str,
    due_at: datetime,
    timezone_name: str,
    recurrence: str = Recurrence.ONE_OFF,
    details: str = "",
    task: Task | None = None,
    weekday: int | None = None,
    allow_during_quiet_hours: bool = False,
) -> Reminder:
    local = due_at.astimezone(tzinfo_of(timezone_name))
    reminder = Reminder.objects.create(
        user=user,
        task=task,
        title=title,
        details=details,
        timezone=timezone_name,
        due_at=due_at,
        local_date=local.date(),
        local_time=local.time().replace(microsecond=0),
        recurrence=recurrence,
        weekday=weekday if weekday is not None else local.weekday(),
        allow_during_quiet_hours=allow_during_quiet_hours,
    )
    if task:
        add_evidence(
            task,
            evidence_type=EvidenceType.IN_APP_RECORD,
            summary_fa=f"یادآور «{title}» در برنامه ثبت شد.",
            proves="reminder_created",
            origin="system",
        )
        set_outcome(task, "not_submitted")
        transition(task, ExecutionState.DELIVERED, activity_fa="یادآور ساخته شد")
    return reminder


def display_when(reminder: Reminder) -> str:
    return format_jalali_fa(reminder.due_at.astimezone(tzinfo_of(reminder.timezone)), include_time=True)


def cancel_reminder(reminder: Reminder, *, record: bool = True) -> Reminder:
    reminder.cancelled_at = timezone.now()
    reminder.save(update_fields=["cancelled_at"])
    if record and reminder.task_id:
        append_event(reminder.task, "reminder_cancelled", "یادآور لغو شد؛ نوتیفیکیشن آینده ارسال نمی‌شود.")
        transition(reminder.task, ExecutionState.CANCELLED, activity_fa="یادآور لغو شد")
    return reminder


def complete_reminder(reminder: Reminder) -> Reminder:
    reminder.completed_at = timezone.now()
    reminder.save(update_fields=["completed_at"])
    return reminder


def reopen_reminder(reminder: Reminder) -> Reminder:
    reminder.completed_at = None
    reminder.cancelled_at = None
    reminder.save(update_fields=["completed_at", "cancelled_at"])
    return reminder


def delete_reminder(reminder: Reminder) -> None:
    reminder.deleted_at = timezone.now()
    reminder.save(update_fields=["deleted_at"])


def edit_recurrence(reminder: Reminder, *, scope: str, new_due_at: datetime | None = None, title: str | None = None):
    """scope: this_occurrence | this_and_future"""
    if reminder.recurrence == Recurrence.ONE_OFF or scope == "this_and_future":
        if new_due_at:
            local = new_due_at.astimezone(tzinfo_of(reminder.timezone))
            reminder.due_at = new_due_at
            reminder.local_date = local.date()
            reminder.local_time = local.time().replace(microsecond=0)
        if title:
            reminder.title = title
        reminder.save()
        return reminder
    if scope == "this_occurrence":
        ReminderOccurrenceEdit.objects.create(
            reminder=reminder,
            occurrence_at=reminder.due_at,
            action="skip" if new_due_at is None else "reschedule",
            new_due_at=new_due_at,
        )
        if new_due_at is None:
            _advance_recurring(reminder)
        return reminder
    raise ValueError("باید این نوبت یا این نوبت و نوبت‌های بعد را انتخاب کنید.")


def _advance_recurring(reminder: Reminder) -> None:
    if reminder.recurrence == Recurrence.DAILY:
        reminder.due_at = reminder.due_at + timedelta(days=1)
    elif reminder.recurrence == Recurrence.WEEKLY:
        reminder.due_at = reminder.due_at + timedelta(days=7)
    else:
        return
    local = reminder.due_at.astimezone(tzinfo_of(reminder.timezone))
    reminder.local_date = local.date()
    reminder.local_time = local.time().replace(microsecond=0)
    reminder.save()


def due_queryset(now: datetime | None = None):
    now = now or timezone.now()
    return Reminder.objects.filter(
        cancelled_at__isnull=True,
        completed_at__isnull=True,
        deleted_at__isnull=True,
        due_at__lte=now,
    ).exclude(last_fired_at__isnull=False, recurrence=Recurrence.ONE_OFF)


def fire_due_reminders(now: datetime | None = None) -> int:
    from apps.notifications.services import notify_reminder

    now = now or timezone.now()
    count = 0
    for reminder in due_queryset(now):
        skip = ReminderOccurrenceEdit.objects.filter(
            reminder=reminder, occurrence_at=reminder.due_at, action="skip"
        ).exists()
        override = ReminderOccurrenceEdit.objects.filter(
            reminder=reminder, occurrence_at=reminder.due_at, action="reschedule"
        ).first()
        if skip:
            reminder.last_fired_at = now
            reminder.save(update_fields=["last_fired_at"])
            if reminder.recurrence != Recurrence.ONE_OFF:
                _advance_recurring(reminder)
            continue
        fire_at = override.new_due_at if override and override.new_due_at else reminder.due_at
        if fire_at > now:
            continue
        notify_reminder(reminder)
        reminder.last_fired_at = now
        reminder.save(update_fields=["last_fired_at"])
        if reminder.recurrence != Recurrence.ONE_OFF:
            _advance_recurring(reminder)
        count += 1
    return count


def apply_timezone_change(user: User, old_tz: str, new_tz: str, choice: str) -> None:
    qs = Reminder.objects.filter(user=user, cancelled_at__isnull=True, deleted_at__isnull=True)
    for reminder in qs:
        if choice == "keep_local_clock":
            reminder.due_at = shift_keep_local_clock(reminder.due_at, old_tz, new_tz)
        else:
            reminder.due_at = shift_keep_instant(reminder.due_at, new_tz)
        reminder.timezone = new_tz
        local = reminder.due_at.astimezone(tzinfo_of(new_tz))
        reminder.local_date = local.date()
        reminder.local_time = local.time().replace(microsecond=0)
        reminder.save()


def serialize_reminder(reminder: Reminder) -> dict:
    return {
        "id": reminder.id,
        "title": reminder.title,
        "details": reminder.details,
        "timezone": reminder.timezone,
        "due_at": reminder.due_at.isoformat(),
        "display_fa": display_when(reminder),
        "jalali_time": to_persian_digits(
            reminder.due_at.astimezone(tzinfo_of(reminder.timezone)).strftime("%H:%M")
        ),
        "recurrence": reminder.recurrence,
        "cancelled": reminder.cancelled_at is not None,
        "completed": reminder.completed_at is not None,
        "task_id": reminder.task_id,
        "allow_during_quiet_hours": reminder.allow_during_quiet_hours,
    }


def agenda(user: User, *, view: str, on_date=None) -> dict:
    """Today / Upcoming / date. Only this product's events."""
    from datetime import date as date_cls

    tz = tzinfo_of(user.timezone)
    today = timezone.now().astimezone(tz).date()
    qs = Reminder.objects.filter(user=user, deleted_at__isnull=True, cancelled_at__isnull=True)
    items = []
    for r in qs:
        local_day = r.due_at.astimezone(tz).date()
        if view == "today" and local_day != today:
            continue
        if view == "upcoming" and local_day < today:
            continue
        if view == "date" and on_date:
            if isinstance(on_date, str):
                on_date = date_cls.fromisoformat(on_date)
            if local_day != on_date:
                continue
        items.append(serialize_reminder(r))
    return {
        "view": view,
        "disclaimer_fa": "این برنامه فقط رویدادهای همین محصول است و تقویم خارجی همگام نیست.",
        "items": items,
    }
