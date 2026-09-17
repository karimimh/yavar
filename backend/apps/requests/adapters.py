"""Sandbox nonbinding oil-change request form. Local HTML fixture preferred for CI."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

_force_timeout_after_send = False
_force_deposit = False
_force_captcha = False
_force_unexpected_domain = False
_force_new_terms = False
_submissions: dict[str, dict] = {}


def reset() -> None:
    global _force_timeout_after_send, _force_deposit, _force_captcha
    global _force_unexpected_domain, _force_new_terms, _submissions
    _force_timeout_after_send = False
    _force_deposit = False
    _force_captcha = False
    _force_unexpected_domain = False
    _force_new_terms = False
    _submissions = {}


def set_timeout_after_send(v: bool) -> None:
    global _force_timeout_after_send
    _force_timeout_after_send = v


def set_deposit(v: bool) -> None:
    global _force_deposit
    _force_deposit = v


def set_captcha(v: bool) -> None:
    global _force_captcha
    _force_captcha = v


def set_unexpected_domain(v: bool) -> None:
    global _force_unexpected_domain
    _force_unexpected_domain = v


def set_new_terms(v: bool) -> None:
    global _force_new_terms
    _force_new_terms = v


ALLOWED_DOMAIN = "sandbox.yavar.local"
FORM_DESTINATION = "https://sandbox.yavar.local/service-request"


def inspect_form() -> dict:
    if _force_unexpected_domain:
        return {"ok": False, "needs_user_takeover": True, "reason": "unexpected_domain", "domain": "other.example"}
    if _force_captcha:
        return {"ok": False, "needs_user_takeover": True, "reason": "captcha"}
    if _force_deposit:
        return {
            "ok": False,
            "blocked": True,
            "reason": "deposit",
            "message_fa": "فرم پیش‌پرداخت می‌خواهد؛ ارسال متوقف شد.",
        }
    if _force_new_terms:
        return {
            "ok": False,
            "blocked": True,
            "reason": "binding_terms",
            "message_fa": "شرایط الزام‌آور جدید ظاهر شد؛ ارسال متوقف شد.",
        }
    return {
        "ok": True,
        "destination": FORM_DESTINATION,
        "domain": ALLOWED_DOMAIN,
        "nonbinding": True,
        "fields": ["name", "phone", "area", "preferred_slot", "note"],
        "may_transmit_on_fill": True,
    }


def submit(fields: dict, *, approval_id: int) -> dict:
    key = f"{approval_id}"
    if key in _submissions:
        return {"ok": True, "duplicate": True, **_submissions[key]}
    if _force_timeout_after_send:
        # May have reached provider — caller must mark outcome unknown, no blind retry.
        ref = hashlib.sha256(json.dumps(fields, sort_keys=True).encode()).hexdigest()[:10]
        _submissions[key] = {
            "maybe_received": True,
            "reference": f"UNK-{ref}",
            "received_at": datetime.now(UTC).isoformat(),
        }
        return {"ok": False, "timeout": True, "maybe_received": True, "reference": f"UNK-{ref}"}
    ref = f"SBX-{approval_id}-{len(_submissions)+1}"
    result = {
        "ok": True,
        "sandbox": True,
        "reference": ref,
        "ack_fa": "درخواست دریافت شد؛ نوبت هنوز تأیید نشده است.",
        "appointment_confirmed": False,
        "received_at": datetime.now(UTC).isoformat(),
    }
    _submissions[key] = result
    return result


def reconcile(approval_id: int) -> dict:
    key = f"{approval_id}"
    if key in _submissions:
        return {"known": True, **_submissions[key]}
    return {"known": False}
