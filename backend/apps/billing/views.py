import secrets
from datetime import timedelta

from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.billing.models import Plan, SubscriptionPayment
from apps.billing.services import (
    PRO_PRICE,
    PRO_UNIT,
    ensure_entitlement,
    seed_plans,
    serialize_entitlement,
)
from apps.core.enums import PlanCode


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def plans(request: Request) -> Response:
    seed_plans()
    return Response(
        {
            "current": serialize_entitlement(request.user),
            "pro_price_amount": str(PRO_PRICE),
            "pro_price_unit": PRO_UNIT,
            "pro_price_fa": "۲۹۹٬۰۰۰ تومان / ۳۰ روز",
            "auto_renew": False,
            "sandbox": True,
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def checkout(request: Request) -> Response:
    seed_plans()
    authority = secrets.token_urlsafe(16)
    SubscriptionPayment.objects.create(
        user=request.user,
        authority=authority,
        amount=PRO_PRICE,
        unit=PRO_UNIT,
        status="initiated",
    )
    return Response(
        {
            "sandbox": True,
            "authority": authority,
            "redirect_url": f"/api/billing/sandbox/pay/?authority={authority}",
            "amount": str(PRO_PRICE),
            "unit": PRO_UNIT,
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def sandbox_pay(request: Request) -> Response:
    authority = request.GET.get("authority", "")
    pay = SubscriptionPayment.objects.filter(authority=authority).first()
    if not pay:
        return Response({"error": "not found"}, status=404)
    pay.status = "redirected"
    pay.save(update_fields=["status"])
    # Simulated gateway page then return to app
    return_to = request.GET.get("return") or f"http://localhost:3000/app/account/plans?authority={authority}"
    return Response(
        {
            "sandbox": True,
            "message_fa": "درگاه پرداخت آزمایشی محصول یاور — نه قبض برق یا بلیط.",
            "authority": authority,
            "return_url": return_to,
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def verify(request: Request) -> Response:
    """Treat return, verification, and inquiry as separate. Activate Pro only after verify."""
    authority = (request.data or {}).get("authority")
    pay = SubscriptionPayment.objects.filter(authority=authority, user=request.user).first()
    if not pay:
        return Response({"ok": False, "error": "پرداخت یافت نشد"}, status=404)
    pay.return_seen_at = timezone.now()
    pay.save(update_fields=["return_seen_at"])
    # Inquiry is separate from verification
    inquiry = "paid_sandbox"
    pay.inquiry_status = inquiry
    if pay.status == "verified":
        # Repeated return does not double-activate (AC-46)
        return Response({"ok": True, "already_verified": True, "entitlement": serialize_entitlement(request.user)})
    # Sandbox verify succeeds when redirected
    if pay.status in {"initiated", "redirected"}:
        pay.status = "verified"
        pay.verified_at = timezone.now()
        pay.save(update_fields=["status", "verified_at", "inquiry_status"])
        ent = ensure_entitlement(request.user)
        plan = Plan.objects.get(code=PlanCode.PRO)
        ent.plan = plan
        ent.period_start = timezone.now()
        ent.period_end = timezone.now() + timedelta(days=30)
        ent.pro_activated_at = timezone.now()
        ent.task_runs_reserved = 0
        ent.task_runs_consumed = 0
        ent.sms_consumed = 0
        ent.save()
        return Response({"ok": True, "activated": True, "entitlement": serialize_entitlement(request.user)})
    pay.save(update_fields=["inquiry_status"])
    return Response({"ok": False, "error": "تأیید ناموفق"}, status=400)
