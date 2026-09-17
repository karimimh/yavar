from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.accounts.models import OneTimeCode, OtpThrottle, User
from apps.accounts.sms import ConsoleSmsProvider, MemorySmsProvider, SmsProvider
from apps.core.persian import normalize_phone

OTP_TTL = timedelta(minutes=5)
OTP_WINDOW = timedelta(minutes=10)
MAX_REQUESTS_PER_WINDOW = 5
MAX_VERIFY_ATTEMPTS = 5

_memory_sms = MemorySmsProvider()


def get_sms_provider() -> SmsProvider:
    name = getattr(settings, "SMS_PROVIDER", "console")
    if name == "memory":
        return _memory_sms
    return ConsoleSmsProvider()


def hash_code(code: str) -> str:
    return hmac.new(
        settings.SECRET_KEY.encode(),
        code.encode(),
        hashlib.sha256,
    ).hexdigest()


def _throttle_key(kind: str, value: str) -> str:
    return f"{kind}:{value}"


def check_and_bump_throttle(kind: str, value: str, *, limit: int = MAX_REQUESTS_PER_WINDOW) -> bool:
    """Return True if allowed."""
    now = timezone.now()
    key = _throttle_key(kind, value)
    row, created = OtpThrottle.objects.get_or_create(
        key=key,
        defaults={"window_started_at": now, "count": 0},
    )
    if not created and now - row.window_started_at > OTP_WINDOW:
        row.window_started_at = now
        row.count = 0
    if row.count >= limit:
        return False
    row.count += 1
    row.save(update_fields=["window_started_at", "count"])
    return True


def request_otp(raw_phone: str, *, ip: str | None = None) -> dict:
    """Always return the same public message; never disclose whether the phone exists."""
    try:
        phone, _original = normalize_phone(raw_phone)
    except ValueError:
        # Same response to avoid phone-existence oracle via validation timing/shape? Invalid format
        # can be reported because it is not an account-existence leak.
        return {"ok": False, "error": "شماره موبایل نامعتبر است."}

    if not check_and_bump_throttle("otp_phone", phone):
        return {"ok": True, "message": "اگر این شماره مجاز باشد، کد تأیید ارسال شد."}
    if ip and not check_and_bump_throttle("otp_ip", ip, limit=20):
        return {"ok": True, "message": "اگر این شماره مجاز باشد، کد تأیید ارسال شد."}

    code = f"{secrets.randbelow(1_000_000):06d}"
    OneTimeCode.objects.create(
        phone=phone,
        code_hash=hash_code(code),
        expires_at=timezone.now() + OTP_TTL,
        ip_address=ip,
    )
    get_sms_provider().send(phone, f"YAVAR OTP {code}")
    return {"ok": True, "message": "اگر این شماره مجاز باشد، کد تأیید ارسال شد."}


def verify_otp(raw_phone: str, code: str | None) -> tuple[User | None, str | None]:
    try:
        phone, original = normalize_phone(raw_phone)
    except ValueError:
        return None, "شماره یا کد نامعتبر است."

    supplied = str(code or "").strip()
    otp = (
        OneTimeCode.objects.filter(phone=phone, consumed_at__isnull=True)
        .order_by("-created_at")
        .first()
    )
    if otp is None or timezone.now() > otp.expires_at:
        return None, "شماره یا کد نامعتبر است."
    if otp.attempt_count >= MAX_VERIFY_ATTEMPTS:
        return None, "شماره یا کد نامعتبر است."
    otp.attempt_count += 1
    if not hmac.compare_digest(otp.code_hash, hash_code(supplied)):
        otp.save(update_fields=["attempt_count"])
        return None, "شماره یا کد نامعتبر است."

    otp.consumed_at = timezone.now()
    otp.save(update_fields=["attempt_count", "consumed_at"])
    user, _created = User.objects.get_or_create(phone=phone, defaults={"phone_original": original})
    return user, None
