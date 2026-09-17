from celery import shared_task
from django.utils import timezone


@shared_task
def tick_due_reminders() -> int:
    from apps.reminders.services import fire_due_reminders

    return fire_due_reminders()


@shared_task
def continue_task(task_id: int) -> None:
    from apps.agent.runtime import continue_background

    continue_background(task_id)


@shared_task
def purge_expired_screenshots() -> int:
    from datetime import timedelta

    from apps.conversations.models import Attachment

    cutoff = timezone.now() - timedelta(days=7)
    n = 0
    for att in Attachment.objects.filter(retain_original=False, original_deleted_at__isnull=True, created_at__lt=cutoff):
        att.file.delete(save=False)
        att.original_deleted_at = timezone.now()
        att.save(update_fields=["original_deleted_at"])
        n += 1
    return n


@shared_task
def purge_temporary_identifiers() -> int:
    from datetime import timedelta

    from apps.core.enums import TERMINAL_EXECUTION_STATES
    from apps.tasks.models import Task

    cutoff = timezone.now() - timedelta(hours=24)
    n = 0
    for task in Task.objects.filter(updated_at__lt=cutoff, execution_state__in=TERMINAL_EXECUTION_STATES):
        payload = dict(task.payload)
        changed = False
        for key in ("bill_id", "pending_value"):
            if key in payload:
                payload[key] = "***"
                changed = True
        if changed:
            task.payload = payload
            task.save(update_fields=["payload"])
            n += 1
    return n
