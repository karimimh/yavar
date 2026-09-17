from rest_framework.decorators import api_view, permission_classes
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.models import User
from apps.billing.services import restore_run
from apps.coverage.models import Capability, OperatorSettings
from apps.operators.models import AuditLog, SafetyIncident, SupportIncident
from apps.operators.permissions import IsOperator
from apps.tasks.models import Task


def _audit(request, action: str, target_type: str, target_id: str, summary_fa: str, data=None):
    AuditLog.objects.create(
        actor=request.user,
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        summary_fa=summary_fa,
        data=data or {},
    )


@api_view(["GET"])
@permission_classes([IsOperator])
def dashboard(request: Request) -> Response:
    return Response(
        {
            "pause_all_external_submissions": OperatorSettings.get().pause_all_external_submissions,
            "capabilities": [
                {"slug": c.slug, "operator_disabled": c.operator_disabled, "status": c.effective_status()}
                for c in Capability.objects.all()
            ],
            "unknown_outcomes": Task.objects.filter(execution_state="outcome_unknown").count(),
            "incidents": SupportIncident.objects.count(),
        }
    )


@api_view(["POST"])
@permission_classes([IsOperator])
def disable_capability(request: Request) -> Response:
    slug = (request.data or {}).get("slug")
    cap = Capability.objects.filter(slug=slug).first()
    if not cap:
        return Response({"error": "یافت نشد"}, status=404)
    cap.operator_disabled = bool(request.data.get("disabled", True))
    cap.save(update_fields=["operator_disabled"])
    _audit(request, "disable_capability", "capability", slug, f"قابلیت {slug} غیرفعال/فعال شد")
    return Response({"ok": True, "slug": slug, "disabled": cap.operator_disabled})


@api_view(["POST"])
@permission_classes([IsOperator])
def pause_submissions(request: Request) -> Response:
    s = OperatorSettings.get()
    s.pause_all_external_submissions = bool(request.data.get("paused", True))
    s.save()
    _audit(request, "pause_submissions", "global", "1", "توقف همهٔ ارسال‌های خارجی")
    return Response({"ok": True, "paused": s.pause_all_external_submissions})


@api_view(["POST"])
@permission_classes([IsOperator])
def suspend_account(request: Request) -> Response:
    user = User.objects.filter(id=(request.data or {}).get("user_id")).first()
    if not user:
        return Response({"error": "یافت نشد"}, status=404)
    user.is_suspended = True
    user.save(update_fields=["is_suspended"])
    _audit(request, "suspend_account", "user", str(user.id), "تعلیق حساب")
    return Response({"ok": True})


@api_view(["POST"])
@permission_classes([IsOperator])
def restore_credits(request: Request) -> Response:
    user = User.objects.filter(id=(request.data or {}).get("user_id")).first()
    if not user:
        return Response({"error": "یافت نشد"}, status=404)
    restore_run(user, task_id=request.data.get("task_id"), reason="operator_restore")
    _audit(request, "restore_credits", "user", str(user.id), "بازگردانی سهمیه")
    return Response({"ok": True})


@api_view(["GET"])
@permission_classes([IsOperator])
def incident_trail(request: Request, pk: int) -> Response:
    inc = SupportIncident.objects.filter(id=pk).first()
    if not inc:
        return Response({"error": "یافت نشد"}, status=404)
    _audit(request, "inspect_incident", "incident", str(pk), "بازرسی رد حادثهٔ خلاصه‌شده")
    return Response(
        {
            "id": inc.id,
            "redacted_context": inc.redacted_context,
            "message": inc.message[:500],
            "task_id": inc.task_id if inc.consent_share_task else None,
        }
    )


@api_view(["POST"])
@permission_classes([IsOperator])
def open_task(request: Request, pk: int) -> Response:
    """AC-44: deny unrelated user tasks unless this is the consented support incident task."""
    task = Task.objects.filter(id=pk).first()
    if not task:
        return Response({"error": "یافت نشد"}, status=404)
    allowed = SupportIncident.objects.filter(
        task=task, consent_share_task=True
    ).exists()
    if not allowed:
        _audit(request, "denied_task_access", "task", str(pk), "دسترسی به کار نامرتبط رد شد")
        return Response({"error": "دسترسی به کار این کاربر مجاز نیست."}, status=403)
    _audit(request, "open_consented_task", "task", str(pk), "مشاهدهٔ کار با رضایت گزارش")
    return Response({"id": task.id, "title": task.title, "state": task.execution_state})


def record_safety_incident(kind: str, capability_slug: str, summary_fa: str) -> None:
    SafetyIncident.objects.create(kind=kind, capability_slug=capability_slug, summary_fa=summary_fa)
    cap = Capability.objects.filter(slug=capability_slug).first()
    if cap:
        cap.operator_disabled = True
        cap.save(update_fields=["operator_disabled"])
