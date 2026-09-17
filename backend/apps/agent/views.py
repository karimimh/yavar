from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.enums import TaskKind
from apps.reminders.services import create_reminder
from apps.tasks.models import Task
from apps.tasks.state import serialize_task, transition


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def confirm_extraction(request: Request, pk: int) -> Response:
    task = Task.objects.filter(id=pk, user=request.user, kind=TaskKind.EXTRACTION).first()
    if not task:
        return Response({"error": "یافت نشد"}, status=404)
    selected = set(request.data.get("selected_indexes") or [])
    draft = (task.payload or {}).get("extraction_draft") or {}
    created = []
    for i, item in enumerate(draft.get("items") or []):
        if i not in selected:
            continue
        if item.get("amount_uncertain") and not item.get("amount"):
            # still allow creating the obligation without amount
            pass
        from datetime import datetime


        due = None
        if item.get("due_at"):
            due = datetime.fromisoformat(item["due_at"])
        if due is None:
            continue
        rem_task = Task.objects.create(
            user=request.user,
            kind=TaskKind.REMINDER,
            title=item.get("title", "یادآور"),
            original_goal=item.get("excerpt", ""),
            agreed_deliverable="یادآور بازبینی‌شده از تصویر",
            conversation=task.conversation,
        )
        create_reminder(
            user=request.user,
            title=item.get("title", "یادآور"),
            due_at=due,
            timezone_name=request.user.timezone,
            task=rem_task,
        )
        created.append(rem_task.id)
    payload = dict(task.payload)
    payload["extraction_draft"] = {**draft, "saved": True, "created_task_ids": created}
    task.payload = payload
    task.save(update_fields=["payload"])
    transition(task, "delivered", activity_fa="موارد انتخاب‌شده ساخته شد")
    return Response({"ok": True, "created_task_ids": created, "task": serialize_task(task)})
