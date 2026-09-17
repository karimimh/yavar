from datetime import datetime, time

from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.services import get_sms_provider
from apps.billing.services import consume_sms, ensure_entitlement, remaining_sms
from apps.notifications.models import Notification
from apps.reminders.models import Reminder


def _in_quiet_hours(user: User, when: datetime) -> bool:
    if not user.quiet_hours_start or not user.quiet_hours_end:
        return False
    local = when.astimezone()
    t = local.timetz() if False else local.time()
    start: time = user.quiet_hours_start
    end: time = user.quiet_hours_end
    if start <= end:
        return start <= t <= end
    return t >= start or t <= end


def notify_inbox(
    user: User,
    *,
    title_fa: str,
    body_fa: str,
    task=None,
    reminder=None,
    sms: bool = False,
) -> Notification:
    n = Notification.objects.create(
        user=user,
        task=task,
        reminder=reminder,
        channel="inbox",
        title_fa=title_fa,
        body_fa=body_fa,
        delivery_status="delivered",
    )
    if sms:
        _maybe_sms(user, n)
    return n


def _maybe_sms(user: User, notification: Notification) -> None:
    if not user.sms_opt_in:
        return
    ensure_entitlement(user)
    if remaining_sms(ensure_entitlement(user)) <= 0:
        notification.delivery_status = "skipped_sms_exhausted"
        notification.save(update_fields=["delivery_status"])
        return
    body = "یکی از کارهایت به توجه نیاز دارد"
    get_sms_provider().send(user.phone, body)
    consume_sms(user)
    Notification.objects.create(
        user=user,
        task=notification.task,
        reminder=notification.reminder,
        channel="sms",
        title_fa="پیامک",
        body_fa=body,
        generic_sms_body=body,
        delivery_status="accepted",
    )


def notify_reminder(reminder: Reminder) -> Notification | None:
    user = reminder.user
    now = timezone.now()
    if _in_quiet_hours(user, now) and not reminder.allow_during_quiet_hours:
        return Notification.objects.create(
            user=user,
            reminder=reminder,
            channel="inbox",
            title_fa="یادآور (ساعت سکوت)",
            body_fa=reminder.title,
            delivery_status="skipped_quiet_hours",
        )
    n = notify_inbox(
        user,
        title_fa="یادآور",
        body_fa=reminder.title,
        reminder=reminder,
        task=reminder.task,
        sms=True,
    )
    return n


def serialize_notification(n: Notification) -> dict:
    return {
        "id": n.id,
        "title_fa": n.title_fa,
        "body_fa": n.body_fa,
        "channel": n.channel,
        "read": n.read_at is not None,
        "delivery_status": n.delivery_status,
        "task_id": n.task_id,
        "created_at": n.created_at.isoformat(),
    }
