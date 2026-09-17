from datetime import UTC, datetime

LIVE_OK = {
    "THRHOME01": {
        "label_fa": "برق خانه (سندباکس)",
        "amount": "185000",
        "unit": "toman",
        "period_fa": "مرداد ۱۴۰۵",
        "due_date": "2026-09-25",
        "retrieved_at": datetime(2026, 9, 17, 9, 0, tzinfo=UTC).isoformat(),
        "provider_fa": "استعلام برق آزمایشی",
        "payment_url": "https://sandbox.yavar.local/bills/pay/THRHOME01",
        "payment_domain": "sandbox.yavar.local",
    }
}

_fail_live = False
_unexpected_redirect = False


def set_live_fail(value: bool) -> None:
    global _fail_live
    _fail_live = value


def set_unexpected_redirect(value: bool) -> None:
    global _unexpected_redirect
    _unexpected_redirect = value


def inquire(bill_id: str) -> dict:
    if _fail_live:
        return {"ok": False, "error_fa": "استعلام زنده در دسترس نیست."}
    data = LIVE_OK.get(bill_id)
    if not data:
        return {"ok": False, "error_fa": "شناسه در سندباکس یافت نشد."}
    return {"ok": True, "sandbox": True, "sandbox_label_fa": "آزمایشی", **data}


def payment_handoff(bill_id: str) -> dict:
    data = inquire(bill_id)
    if not data.get("ok"):
        return data
    url = data["payment_url"]
    domain = data["payment_domain"]
    if _unexpected_redirect:
        return {
            "ok": False,
            "pause": True,
            "error_fa": "مقصد پرداخت غیرمنتظره است؛ اطلاعات خصوصی ارسال نشد.",
            "seen_domain": "evil.example",
            "expected_domain": domain,
        }
    return {
        "ok": True,
        "sandbox": True,
        "url": url,
        "amount": data["amount"],
        "unit": data["unit"],
        "fee_fa": "کارمزد درگاه در سندباکس نامشخص است و صفر فرض نمی‌شود.",
        "provider_fa": data["provider_fa"],
        "disclaimer_fa": "بازگشت از صفحهٔ پرداخت به معنی پرداخت موفق نیست. یاور کارت یا رمز وارد نمی‌کند.",
    }
