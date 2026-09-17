from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.approvals.models import Approval
from apps.approvals.services import approve, begin_submission, serialize_approval
from apps.core.enums import EvidenceType, ExecutionState, ExternalOutcome
from apps.coverage.services import require_executable
from apps.requests import adapters as request_adapters
from apps.tasks.state import add_evidence, append_event, set_outcome, transition


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def approval_detail(request: Request, pk: int) -> Response:
    approval = Approval.objects.filter(id=pk, user=request.user).first()
    if not approval:
        return Response({"error": "یافت نشد"}, status=404)
    return Response(serialize_approval(approval))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def approval_decide(request: Request, pk: int) -> Response:
    approval = Approval.objects.filter(id=pk, user=request.user).first()
    if not approval:
        return Response({"error": "یافت نشد"}, status=404)
    action = (request.data or {}).get("action")
    if action == "cancel":
        approval.status = "cancelled"
        approval.save(update_fields=["status"])
        transition(approval.task, ExecutionState.CANCELLED, activity_fa="تأیید لغو شد")
        return Response(serialize_approval(approval))
    if action == "edit":
        fields = request.data.get("fields") or approval.fields_snapshot
        from apps.approvals.services import invalidate_if_changed

        invalidate_if_changed(approval, fields)
        draft = approval.task.drafts.order_by("-id").first()
        if draft:
            draft.fields = fields
            draft.save(update_fields=["fields"])
        latest = approval.task.approvals.order_by("-id").first()
        return Response(serialize_approval(latest))
    if action != "approve":
        return Response({"error": "اقدام نامعتبر"}, status=400)
    approval.refresh_from_db()
    if approval.attempt_started or approval.status == "used":
        recon = request_adapters.reconcile(approval.id)
        return Response(
            {
                "ok": True,
                "duplicate_prevented": True,
                "reconciliation": recon,
                "approval": serialize_approval(approval),
            }
        )
    ok, err = approve(approval)
    if not ok:
        return Response({"ok": False, "error": err, "approval": serialize_approval(approval)}, status=400)
    # Filling may transmit before submit — require fill consent if flagged.
    if approval.task.payload.get("needs_fill_consent") and not request.data.get("fill_consent"):
        return Response(
            {
                "ok": False,
                "needs_fill_consent": True,
                "message_fa": "پر کردن فرم ممکن است داده را قبل از ارسال نهایی منتقل کند. رضایت جدا لازم است.",
            },
            status=400,
        )
    return _attempt_submit(approval)


def _attempt_submit(approval: Approval) -> Response:
    ok_cap, info = require_executable("local_service_request")
    if not ok_cap:
        return Response({"ok": False, "error": info["label_fa"]}, status=400)
    allowed, reason = begin_submission(approval)
    if not allowed and reason == "already_attempted":
        recon = request_adapters.reconcile(approval.id)
        return Response(
            {
                "ok": True,
                "duplicate_prevented": True,
                "reconciliation": recon,
                "approval": serialize_approval(approval),
            }
        )
    if not allowed:
        return Response({"ok": False, "error": reason}, status=400)
    form = request_adapters.inspect_form()
    if form.get("blocked"):
        transition(approval.task, ExecutionState.BLOCKED, activity_fa=form["message_fa"])
        return Response({"ok": False, "blocked": True, "message_fa": form["message_fa"]})
    if form.get("needs_user_takeover"):
        transition(approval.task, ExecutionState.NEEDS_USER_TAKEOVER, activity_fa="نیاز به ادامه توسط شما")
        return Response({"ok": False, "needs_user_takeover": True, "reason": form.get("reason")})
    transition(approval.task, ExecutionState.CHECKING_RESULT, activity_fa="در حال ارسال درخواست آزمایشی")
    result = request_adapters.submit(approval.fields_snapshot, approval_id=approval.id)
    if result.get("timeout"):
        set_outcome(
            approval.task,
            ExternalOutcome.UNKNOWN,
            remaining="ارسال ممکن است رسیده باشد؛ ارسال مجدد کورکورانه انجام نمی‌شود.",
        )
        transition(approval.task, ExecutionState.OUTCOME_UNKNOWN, activity_fa="نتیجه نامشخص")
        append_event(approval.task, "submit_timeout", "زمان ارسال تمام شد؛ امکان دریافت در سمت ارائه‌دهنده هست.")
        return Response({"ok": False, "outcome": "unknown", "task_id": approval.task_id})
    if approval.task.stop_requested_at:
        recon = request_adapters.reconcile(approval.id)
        transition(approval.task, ExecutionState.CHECKING_RESULT, activity_fa="توقف؛ در حال بررسی دریافت درخواست")
        if recon.get("ok") or recon.get("reference"):
            set_outcome(approval.task, ExternalOutcome.REQUEST_RECEIVED, remaining="بازگشت کامل ادعا نمی‌شود.")
            add_evidence(
                approval.task,
                evidence_type=EvidenceType.PROVIDER_REFERENCE,
                summary_fa="احتمالاً درخواست رسیده؛ لغو به معنی پس‌گرفتن از ارائه‌دهنده نیست.",
                proves="request_submitted",
                reference=recon.get("reference", ""),
                origin="provider",
            )
        return Response({"ok": True, "reconciling": True, "reversed": False})
    add_evidence(
        approval.task,
        evidence_type=EvidenceType.PROVIDER_RECEIPT,
        summary_fa=result.get("ack_fa", "درخواست دریافت شد"),
        proves="request_submitted",
        reference=result.get("reference", ""),
        origin="provider",
        data={"sandbox": True, "appointment_confirmed": False},
    )
    set_outcome(
        approval.task,
        ExternalOutcome.REQUEST_RECEIVED,
        remaining="نوبت هنوز تأیید نشده است.",
    )
    transition(approval.task, ExecutionState.DELIVERED, activity_fa="درخواست دریافت شد؛ نوبت تأیید نشده")
    from apps.billing.services import consume_run

    if approval.task.allowance_reserved and not approval.task.allowance_consumed:
        consume_run(approval.task.user, task_id=approval.task.id, reason="request_submitted")
        approval.task.allowance_consumed = True
        approval.task.save(update_fields=["allowance_consumed"])
    return Response({"ok": True, "reference": result.get("reference"), "appointment_confirmed": False})
