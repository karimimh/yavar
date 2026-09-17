from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.bills import adapters as bill_adapters
from apps.core.enums import EvidenceType, ExecutionState, ExternalOutcome, TaskKind
from apps.tasks.models import Task
from apps.tasks.state import add_evidence, set_outcome, transition


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def payment_handoff(request: Request, pk: int) -> Response:
    task = Task.objects.filter(id=pk, user=request.user).first()
    if not task:
        return Response({"error": "یافت نشد"}, status=404)
    live = task.payload.get("live_bill") or {}
    identifier = task.payload.get("bill_id")
    if not identifier and task.payload.get("pending_alias"):
        from apps.memory.models import SavedFact

        fact = SavedFact.objects.filter(
            user=request.user, kind="bill_alias", label=task.payload["pending_alias"]
        ).first()
        identifier = fact.value if fact else None
    if not identifier and live:
        identifier = "THRHOME01"
    result = bill_adapters.payment_handoff(identifier or "")
    if result.get("pause"):
        transition(task, ExecutionState.NEEDS_USER_TAKEOVER, activity_fa=result["error_fa"])
        return Response(result, status=409)
    if not result.get("ok"):
        return Response(result, status=400)
    task.kind = TaskKind.BILL_HANDOFF
    task.payload["payment_handoff"] = result
    task.save()
    add_evidence(
        task,
        evidence_type=EvidenceType.HANDOFF_PREPARED,
        summary_fa="تحویل پرداخت آزمایشی آماده شد. پرداخت تأیید نشده است.",
        proves="handoff_prepared",
        origin="system",
    )
    set_outcome(task, ExternalOutcome.PREPARED_ONLY, remaining="پرداخت تأیید نشده است.")
    transition(task, ExecutionState.DELIVERED, activity_fa="تحویل پرداخت آماده — پرداخت تأیید نشده")
    return Response({**result, "paid": False, "verified": False})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def payment_return(request: Request, pk: int) -> Response:
    task = Task.objects.filter(id=pk, user=request.user).first()
    if not task:
        return Response({"error": "یافت نشد"}, status=404)
    set_outcome(task, ExternalOutcome.PREPARED_ONLY, remaining="بازگشت از صفحه پرداخت به معنی پرداخت موفق نیست.")
    return Response(
        {
            "paid": False,
            "verified": False,
            "message_fa": "پرداخت تأیید نشده است. تلاش دوم خودکار انجام نمی‌شود.",
        }
    )
