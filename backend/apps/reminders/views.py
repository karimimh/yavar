from datetime import datetime

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.dates import tzinfo_of
from apps.core.enums import ExecutionState, Recurrence, TaskKind
from apps.reminders.models import Reminder
from apps.reminders.services import (
    agenda,
    cancel_reminder,
    complete_reminder,
    create_reminder,
    delete_reminder,
    edit_recurrence,
    serialize_reminder,
)
from apps.tasks.models import Task
from apps.tasks.state import serialize_task, transition


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def reminder_list(request: Request) -> Response:
    if request.method == "GET":
        qs = Reminder.objects.filter(user=request.user, deleted_at__isnull=True)
        return Response({"reminders": [serialize_reminder(r) for r in qs]})
    data = request.data or {}
    due = datetime.fromisoformat(data["due_at"])
    if due.tzinfo is None:
        due = due.replace(tzinfo=tzinfo_of(request.user.timezone))
    task = Task.objects.create(
        user=request.user,
        kind=TaskKind.REMINDER,
        title=data.get("title", "یادآور"),
        original_goal=data.get("title", "یادآور"),
        agreed_deliverable="ایجاد یادآور داخل برنامه",
        original_wording=data.get("title", ""),
    )
    reminder = create_reminder(
        user=request.user,
        title=data.get("title", "یادآور"),
        due_at=due,
        timezone_name=request.user.timezone,
        recurrence=data.get("recurrence", Recurrence.ONE_OFF),
        details=data.get("details", ""),
        task=task,
        allow_during_quiet_hours=bool(data.get("allow_during_quiet_hours")),
    )
    return Response({"reminder": serialize_reminder(reminder), "task": serialize_task(task), "undo": True})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reminder_action(request: Request, pk: int) -> Response:
    reminder = Reminder.objects.filter(id=pk, user=request.user).first()
    if not reminder:
        return Response({"error": "یافت نشد"}, status=404)
    action = (request.data or {}).get("action")
    if action == "cancel":
        cancel_reminder(reminder)
    elif action == "complete":
        complete_reminder(reminder)
    elif action == "delete":
        delete_reminder(reminder)
    elif action == "undo" and reminder.task_id:
        delete_reminder(reminder)
        transition(reminder.task, ExecutionState.CANCELLED, activity_fa="بازنشانی یادآور")
    elif action == "edit_recurrence":
        new_due = request.data.get("due_at")
        due = datetime.fromisoformat(new_due) if new_due else None
        try:
            edit_recurrence(
                reminder,
                scope=request.data.get("scope", "this_and_future"),
                new_due_at=due,
                title=request.data.get("title"),
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=400)
    return Response(serialize_reminder(reminder))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def agenda_view(request: Request) -> Response:
    view = request.GET.get("view", "today")
    on_date = request.GET.get("date")
    return Response(agenda(request.user, view=view, on_date=on_date))
