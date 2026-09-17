import json
from datetime import timedelta

from django.http import HttpResponse
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.approvals.models import Approval
from apps.conversations.models import Attachment, Conversation
from apps.memory.models import SavedFact
from apps.reminders.models import Reminder
from apps.tasks.models import Task


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def export_data(request: Request) -> Response:
    user = request.user
    payload = {
        "phone": user.phone,
        "timezone": user.timezone,
        "preferences": {
            "sms_opt_in": user.sms_opt_in,
            "week_starts_on": user.week_starts_on,
            "improvement_consent": user.improvement_consent,
        },
        "conversations": [
            {
                "id": c.id,
                "title": c.title,
                "messages": [{"role": m.role, "text": m.text, "at": m.created_at.isoformat()} for m in c.messages.all()],
            }
            for c in Conversation.objects.filter(user=user, deleted_at__isnull=True)
        ],
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "state": t.execution_state,
                "outcome": t.external_outcome,
                "goal": t.original_goal,
            }
            for t in Task.objects.filter(user=user)
        ],
        "reminders": [
            {"id": r.id, "title": r.title, "due_at": r.due_at.isoformat()}
            for r in Reminder.objects.filter(user=user, deleted_at__isnull=True)
        ],
        "saved_facts": [{"label": f.label, "value": f.value} for f in SavedFact.objects.filter(user=user)],
        "receipts": [
            {"task_id": t.id, "evidence": [{"summary": e.summary_fa, "type": e.evidence_type} for e in t.evidence.all()]}
            for t in Task.objects.filter(user=user)
        ],
        "secrets_excluded": True,
    }
    body = json.dumps(payload, ensure_ascii=False, indent=2)
    resp = HttpResponse(body, content_type="application/json; charset=utf-8")
    resp["Content-Disposition"] = 'attachment; filename="yavar-export.json"'
    return resp


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def delete_account(request: Request) -> Response:
    user = request.user
    now = timezone.now()
    Approval.objects.filter(user=user, status__in=["pending", "approved"]).update(status="cancelled")
    Reminder.objects.filter(user=user, cancelled_at__isnull=True).update(cancelled_at=now)
    Task.objects.filter(user=user).exclude(
        execution_state__in=["delivered", "cancelled", "failed", "outcome_unknown"]
    ).update(execution_state="cancelled")
    user.is_active = False
    user.deletion_requested_at = now
    user.deletion_due_at = now + timedelta(days=30)
    user.save()
    from django.contrib.auth import logout

    logout(request)
    return Response(
        {
            "ok": True,
            "message_fa": (
                "کار جدید و یادآور آینده متوقف شد، تأییدها باطل شد. "
                "حذف از سامانه‌های فعال تا ۳۰ روز. پنجرهٔ پشتیبان حداکثر ۹۰ روز است. "
                "حذف اینجا داده‌های ارائه‌دهنده را پاک نمی‌کند."
            ),
            "active_removal_days": 30,
            "backup_window_days": 90,
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def delete_attachment(request: Request, pk: int) -> Response:
    att = Attachment.objects.filter(id=pk, user=request.user).first()
    if not att:
        return Response({"error": "یافت نشد"}, status=404)
    att.file.delete(save=False)
    att.original_deleted_at = timezone.now()
    att.save(update_fields=["original_deleted_at"])
    return Response({"ok": True})
