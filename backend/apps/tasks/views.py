from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.enums import ExecutionState, ExternalOutcome, TaskKind
from apps.reminders.models import Reminder
from apps.reminders.services import (
    cancel_reminder,
    complete_reminder,
    delete_reminder,
    reopen_reminder,
)
from apps.tasks.models import Task
from apps.tasks.state import append_event, request_stop, serialize_task, set_outcome, transition


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def task_list(request: Request) -> Response:
    qs = Task.objects.filter(user=request.user)
    status = request.GET.get("filter")
    if status == "attention":
        qs = qs.filter(
            execution_state__in=[
                ExecutionState.NEEDS_INFORMATION,
                ExecutionState.NEEDS_APPROVAL,
                ExecutionState.NEEDS_USER_TAKEOVER,
                ExecutionState.OUTCOME_UNKNOWN,
            ]
        )
    elif status == "delivered":
        qs = qs.filter(execution_state__in=[ExecutionState.DELIVERED, ExecutionState.PARTIALLY_DELIVERED])
    elif status == "closed":
        qs = qs.filter(
            execution_state__in=[
                ExecutionState.CANCELLED,
                ExecutionState.FAILED,
                ExecutionState.EXPIRED,
                ExecutionState.BLOCKED,
            ]
        )
    q = request.GET.get("q")
    if q:
        qs = qs.filter(title__icontains=q)
    return Response({"tasks": [serialize_task(t) for t in qs[:100]]})


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def task_detail(request: Request, pk: int) -> Response:
    task = Task.objects.filter(id=pk, user=request.user).first()
    if not task:
        return Response({"error": "یافت نشد"}, status=404)
    if request.method == "GET":
        return Response(serialize_task(task))
    action = (request.data or {}).get("action")
    if action == "stop":
        request_stop(task)
    elif action == "complete":
        if task.kind in {TaskKind.REMINDER, TaskKind.PERSONAL, TaskKind.BILL_INQUIRY, TaskKind.BILL_HANDOFF}:
            set_outcome(task, ExternalOutcome.USER_REPORTED_COMPLETE)
            transition(task, ExecutionState.DELIVERED, activity_fa="تکمیل به گزارش کاربر")
            rem = Reminder.objects.filter(task=task).first()
            if rem:
                complete_reminder(rem)
    elif action == "reopen":
        rem = Reminder.objects.filter(task=task).first()
        if rem:
            reopen_reminder(rem)
        transition(task, ExecutionState.QUEUED, activity_fa="بازگشایی شد")
    elif action == "cancel":
        rem = Reminder.objects.filter(task=task).first()
        if rem:
            cancel_reminder(rem)
        else:
            request_stop(task)
            transition(task, ExecutionState.CANCELLED, activity_fa="لغو شد")
    elif action == "delete":
        rem = Reminder.objects.filter(task=task).first()
        if rem:
            delete_reminder(rem)
        task.payload["deleted"] = True
        task.save(update_fields=["payload"])
        transition(task, ExecutionState.CANCELLED, activity_fa="حذف شد")
    elif action == "user_paid":
        set_outcome(
            task,
            ExternalOutcome.USER_REPORTED_COMPLETE,
            remaining="پرداخت به گزارش کاربر است؛ تأیید ارائه‌دهنده موجود نیست.",
        )
        append_event(task, "user_paid", "کاربر گفت پرداخت کردم — وضعیت: تکمیل به گزارش کاربر.")
        task.current_activity_fa = "پرداخت تأیید نشده؛ فقط گزارش کاربر"
        task.save(update_fields=["current_activity_fa"])
    elif action == "accept_partial":
        from apps.billing.services import consume_run

        if task.allowance_reserved and not task.allowance_consumed:
            consume_run(task.user, task_id=task.id, reason="partial_accepted")
            task.allowance_consumed = True
            task.save(update_fields=["allowance_consumed"])
        transition(task, ExecutionState.PARTIALLY_DELIVERED, activity_fa="تحویل ناقص پذیرفته شد")
    elif action == "reject_partial":
        from apps.billing.services import restore_run

        if task.allowance_reserved and not task.allowance_consumed:
            restore_run(task.user, task_id=task.id, reason="partial_rejected")
            task.allowance_reserved = False
            task.save(update_fields=["allowance_reserved"])
    return Response(serialize_task(task))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def clarify(request: Request, pk: int) -> Response:
    """Answer a needs_information prompt (mobile/fixed, alias consent, Thursday choice, etc.)."""
    task = Task.objects.filter(id=pk, user=request.user).first()
    if not task:
        return Response({"error": "یافت نشد"}, status=404)
    data = request.data or {}
    payload = dict(task.payload)
    payload.update({k: v for k, v in data.items() if k != "action"})
    task.payload = payload
    task.save(update_fields=["payload"])
    from apps.agent.llm import IntentItem
    from apps.agent.runtime import execute_task

    item = IntentItem(
        kind=task.kind,
        title=task.title,
        original=task.original_wording,
        hard_constraints=task.constraints.get("hard") or {},
        soft_preferences=task.constraints.get("soft") or {},
        payload=payload,
    )
    if data.get("thursday_choice") == "today":
        # Force today by rewriting wording
        item.original = "امروز " + task.original_wording
        item.kind = "reminder"
    elif data.get("thursday_choice") == "next":
        item.original = "پنجشنبه آینده " + task.original_goal
        item.kind = "reminder"
    execute_task(task, item)
    task.refresh_from_db()
    return Response(serialize_task(task))
