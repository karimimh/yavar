from __future__ import annotations

import hashlib
import json
from datetime import timedelta

from django.utils import timezone

from apps.approvals.models import Approval
from apps.core.enums import ExecutionState
from apps.tasks.models import Task
from apps.tasks.state import append_event, transition

APPROVAL_TTL = timedelta(minutes=10)


def fingerprint_payload(payload: dict) -> str:
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()


def create_approval(
    *,
    task: Task,
    action_name: str,
    action_label_fa: str,
    recipient_fa: str,
    destination: str,
    fields_snapshot: dict,
    costs_fa: str,
    will_happen_fa: str,
    will_not_happen_fa: str,
    confirmation_how_fa: str,
) -> Approval:
    fp = fingerprint_payload(fields_snapshot)
    approval = Approval.objects.create(
        user=task.user,
        task=task,
        action_name=action_name,
        action_label_fa=action_label_fa,
        recipient_fa=recipient_fa,
        destination=destination,
        fields_snapshot=fields_snapshot,
        costs_fa=costs_fa,
        will_happen_fa=will_happen_fa,
        will_not_happen_fa=will_not_happen_fa,
        confirmation_how_fa=confirmation_how_fa,
        fingerprint=fp,
        expires_at=timezone.now() + APPROVAL_TTL,
    )
    transition(task, ExecutionState.NEEDS_APPROVAL, activity_fa="در انتظار تأیید دقیق اقدام")
    append_event(task, "approval_created", f"پیش‌نمایش «{action_label_fa}» آماده شد.")
    return approval


def invalidate_if_changed(approval: Approval, new_fields: dict) -> Approval:
    if fingerprint_payload(new_fields) != approval.fingerprint:
        approval.status = "invalidated"
        approval.save(update_fields=["status"])
        append_event(approval.task, "approval_invalidated", "تغییر فیلدها تأیید قبلی را باطل کرد.")
        create_approval(
            task=approval.task,
            action_name=approval.action_name,
            action_label_fa=approval.action_label_fa,
            recipient_fa=approval.recipient_fa,
            destination=approval.destination,
            fields_snapshot=new_fields,
            costs_fa=approval.costs_fa,
            will_happen_fa=approval.will_happen_fa,
            will_not_happen_fa=approval.will_not_happen_fa,
            confirmation_how_fa=approval.confirmation_how_fa,
        )
    return approval


def mark_expired(approval: Approval) -> bool:
    if approval.status in {"pending", "approved"} and timezone.now() > approval.expires_at:
        approval.status = "expired"
        approval.save(update_fields=["status"])
        append_event(approval.task, "approval_expired", "تأیید منقضی شد؛ اجرای دوباره نیاز به تأیید جدید دارد.")
        return True
    return False


def approve(approval: Approval) -> tuple[bool, str]:
    mark_expired(approval)
    approval.refresh_from_db()
    if approval.status == "expired":
        return False, "تأیید منقضی شده است."
    if approval.status != "pending":
        return False, "این تأیید قابل استفاده نیست."
    approval.status = "approved"
    approval.decided_at = timezone.now()
    approval.save(update_fields=["status", "decided_at"])
    append_event(approval.task, "approved", f"کاربر «{approval.action_label_fa}» را تأیید کرد.")
    return True, ""


def begin_submission(approval: Approval) -> tuple[bool, str]:
    """One attempt per approval. Repeated taps reuse the same attempt."""
    mark_expired(approval)
    approval.refresh_from_db()
    if approval.status == "expired":
        return False, "تأیید منقضی شده است؛ اجرای آن مجاز نیست."
    if approval.status not in {"approved", "used"}:
        return False, "تأیید معتبر نیست."
    if approval.attempt_started:
        return False, "already_attempted"
    approval.attempt_started = True
    approval.status = "used"
    approval.used_at = timezone.now()
    approval.save(update_fields=["attempt_started", "status", "used_at"])
    return True, ""


def serialize_approval(approval: Approval) -> dict:
    mark_expired(approval)
    approval.refresh_from_db()
    return {
        "id": approval.id,
        "task_id": approval.task_id,
        "action_name": approval.action_name,
        "action_label_fa": approval.action_label_fa,
        "recipient_fa": approval.recipient_fa,
        "destination": approval.destination,
        "fields_snapshot": approval.fields_snapshot,
        "costs_fa": approval.costs_fa,
        "will_happen_fa": approval.will_happen_fa,
        "will_not_happen_fa": approval.will_not_happen_fa,
        "confirmation_how_fa": approval.confirmation_how_fa,
        "status": approval.status,
        "expires_at": approval.expires_at.isoformat(),
        "attempt_started": approval.attempt_started,
    }
