from django.contrib.auth import login, logout
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.accounts.models import TimezoneChangeProposal, User
from apps.accounts.services import request_otp, verify_otp
from apps.core.dates import DEFAULT_TIMEZONE


def _client_ip(request: Request) -> str | None:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


@ensure_csrf_cookie
@api_view(["GET"])
@permission_classes([AllowAny])
def csrf(request: Request) -> Response:
    token = get_token(request)
    return Response({"csrfToken": token})


@api_view(["POST"])
@permission_classes([AllowAny])
def otp_request(request: Request) -> Response:
    phone = (request.data or {}).get("phone", "")
    result = request_otp(str(phone), ip=_client_ip(request))
    status = 400 if not result.get("ok") else 200
    return Response(result, status=status)


@api_view(["POST"])
@permission_classes([AllowAny])
def otp_verify(request: Request) -> Response:
    data = request.data or {}
    user, error = verify_otp(str(data.get("phone", "")), str(data.get("code", "")))
    if error or user is None:
        return Response({"ok": False, "error": error or "شماره یا کد نامعتبر است."}, status=400)
    if user.is_suspended or not user.is_active:
        return Response({"ok": False, "error": "حساب غیرفعال است."}, status=403)
    login(request, user)
    return Response({"ok": True, "user": serialize_user(user)})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request: Request) -> Response:
    logout(request)
    return Response({"ok": True})


def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "phone": user.phone,
        "phone_original": user.phone_original,
        "preferred_name": user.preferred_name,
        "city": user.city,
        "timezone": user.timezone,
        "week_starts_on": user.week_starts_on,
        "display_currency": user.display_currency,
        "sms_opt_in": user.sms_opt_in,
        "onboarding_completed": user.onboarding_completed_at is not None,
        "quiet_hours_start": user.quiet_hours_start.isoformat() if user.quiet_hours_start else None,
        "quiet_hours_end": user.quiet_hours_end.isoformat() if user.quiet_hours_end else None,
        "improvement_consent": user.improvement_consent,
        "is_operator": user.is_operator,
        "is_staff": user.is_staff,
        "deletion_requested_at": user.deletion_requested_at.isoformat() if user.deletion_requested_at else None,
        "deletion_due_at": user.deletion_due_at.isoformat() if user.deletion_due_at else None,
        "proposed_timezone": DEFAULT_TIMEZONE,
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request: Request) -> Response:
    return Response(serialize_user(request.user))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def complete_onboarding(request: Request) -> Response:
    from django.utils import timezone as dj_tz

    data = request.data or {}
    user: User = request.user
    if not data.get("terms_accepted") or not data.get("privacy_accepted"):
        return Response({"ok": False, "error": "پذیرش شرایط و حریم خصوصی لازم است."}, status=400)
    tz = data.get("timezone") or DEFAULT_TIMEZONE
    user.timezone = tz
    user.sms_opt_in = bool(data.get("sms_opt_in"))
    user.terms_accepted_at = dj_tz.now()
    user.privacy_accepted_at = dj_tz.now()
    user.onboarding_completed_at = dj_tz.now()
    if data.get("week_starts_on"):
        user.week_starts_on = data["week_starts_on"]
    user.save()
    return Response({"ok": True, "user": serialize_user(user)})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_preferences(request: Request) -> Response:

    data = request.data or {}
    user: User = request.user
    if "preferred_name" in data:
        user.preferred_name = str(data["preferred_name"])[:100]
    if "city" in data:
        user.city = str(data["city"])[:100]
    if "usual_departure_city" in data:
        user.usual_departure_city = str(data["usual_departure_city"])[:100]
    if "sms_opt_in" in data:
        user.sms_opt_in = bool(data["sms_opt_in"])
    if "improvement_consent" in data:
        user.improvement_consent = bool(data["improvement_consent"])
    if "week_starts_on" in data:
        user.week_starts_on = str(data["week_starts_on"])
    if "quiet_hours_start" in data:
        user.quiet_hours_start = data["quiet_hours_start"] or None
    if "quiet_hours_end" in data:
        user.quiet_hours_end = data["quiet_hours_end"] or None
    if "default_reminder_time" in data:
        user.default_reminder_time = data["default_reminder_time"] or None
    if "timezone" in data and data["timezone"] != user.timezone:
        proposal = TimezoneChangeProposal.objects.create(
            user=user,
            old_timezone=user.timezone,
            new_timezone=str(data["timezone"]),
        )
        user.save()
        return Response(
            {
                "ok": True,
                "needs_timezone_choice": True,
                "proposal_id": proposal.id,
                "message": "منطقهٔ زمانی عوض شود با حفظ لحظهٔ تقویمی، یا ساعت محلی یادآورها ثابت بماند؟",
                "user": serialize_user(user),
            }
        )
    user.save()
    return Response({"ok": True, "user": serialize_user(user), "needs_timezone_choice": False})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def resolve_timezone_change(request: Request) -> Response:
    from apps.reminders import services as reminder_services

    data = request.data or {}
    try:
        proposal = TimezoneChangeProposal.objects.get(
            id=data.get("proposal_id"), user=request.user, resolved_at__isnull=True
        )
    except TimezoneChangeProposal.DoesNotExist:
        return Response({"ok": False, "error": "درخواست تغییر منطقهٔ زمانی یافت نشد."}, status=404)
    choice = data.get("choice")
    if choice not in {"keep_instant", "keep_local_clock"}:
        return Response({"ok": False, "error": "یکی از دو حالت را انتخاب کنید."}, status=400)
    reminder_services.apply_timezone_change(
        request.user, proposal.old_timezone, proposal.new_timezone, choice
    )
    request.user.timezone = proposal.new_timezone
    request.user.save(update_fields=["timezone"])
    from django.utils import timezone as dj_tz

    proposal.choice = choice
    proposal.resolved_at = dj_tz.now()
    proposal.save(update_fields=["choice", "resolved_at"])
    return Response({"ok": True, "user": serialize_user(request.user)})
