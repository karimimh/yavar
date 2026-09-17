from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.enums import EvidenceType, ExecutionState, ExternalOutcome, TaskKind
from apps.tasks.models import Offer, Task
from apps.tasks.state import add_evidence, append_event, set_outcome, transition
from apps.travel import adapters as travel_adapters


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def select_offer(request: Request, pk: int) -> Response:
    task = Task.objects.filter(id=pk, user=request.user).first()
    if not task:
        return Response({"error": "یافت نشد"}, status=404)
    offer_id = (request.data or {}).get("offer_id")
    offer = Offer.objects.filter(task=task, attributes__id=offer_id).first()
    if offer is None:
        # try payload
        offer = next((o for o in task.offers.all() if (o.attributes or {}).get("id") == offer_id), None)
    if offer is None:
        return Response({"error": "پیشنهاد یافت نشد"}, status=404)
    fresh = travel_adapters.recheck(offer_id)
    old_amount = str(offer.amount) if offer.amount is not None else None
    changed = (
        str(fresh.get("amount")) != old_amount
        or fresh.get("depart_time") != (offer.attributes or {}).get("depart_time")
        or fresh.get("date") != (offer.attributes or {}).get("date")
    )
    if changed:
        append_event(
            task,
            "price_or_offer_changed",
            "قیمت، مسیر یا زمان عوض شده؛ انتخاب جدید لازم است. جایگزینی خاموش انجام نشد.",
            {"old_amount": old_amount, "new_amount": fresh.get("amount")},
        )
        task.payload["changed_offer"] = fresh
        task.save(update_fields=["payload"])
        return Response(
            {
                "changed": True,
                "message_fa": "جزئیات پیشنهاد تغییر کرده است. دوباره انتخاب کنید.",
                "fresh": fresh,
            }
        )
    preserves = fresh.get("preserves_offer", offer.preserves_offer)
    handoff_url = fresh.get("handoff_url") or offer.handoff_url
    note = "ادامه در ارائه‌دهنده"
    remaining = "تحویل آماده‌سازی شد؛ بلیط خریده نشده و رزرو تأیید نشده است."
    if not preserves:
        note = "پیوند به صفحهٔ جستجوی عمومی می‌رود؛ باید پیشنهاد را دوباره انتخاب کنید. این صفحه پرداخت آماده نیست."
    task.kind = TaskKind.TRAVEL_HANDOFF
    task.agreed_deliverable = "آماده‌سازی تحویل به ارائه‌دهنده"
    task.payload["handoff"] = {
        "url": handoff_url,
        "preserves_offer": preserves,
        "sandbox": True,
        "label_fa": "ادامه در ارائه‌دهنده",
        "note_fa": note,
    }
    task.save()
    add_evidence(
        task,
        evidence_type=EvidenceType.HANDOFF_PREPARED,
        summary_fa=note,
        proves="handoff_prepared",
        origin="system",
        data={"url": handoff_url, "sandbox": True},
    )
    set_outcome(task, ExternalOutcome.PREPARED_ONLY, remaining=remaining)
    transition(task, ExecutionState.DELIVERED, activity_fa="تحویل آماده شد — بلیط خریده نشده")
    from apps.billing.services import consume_run

    if task.allowance_reserved and not task.allowance_consumed:
        consume_run(task.user, task_id=task.id, reason="handoff_prepared")
        task.allowance_consumed = True
        task.save(update_fields=["allowance_consumed"])
    return Response(
        {
            "handoff_url": handoff_url,
            "preserves_offer": preserves,
            "label_fa": "ادامه در ارائه‌دهنده",
            "note_fa": note,
            "ticket_purchased": False,
            "sandbox": True,
        }
    )
