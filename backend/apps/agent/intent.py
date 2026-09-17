from __future__ import annotations

import re

from apps.agent.llm import IntentItem, IntentResult
from apps.core.money import is_ambiguous_toman_phrase, parse_budget_phrase
from apps.core.persian import fold_persian, looks_like_otp_or_secret, to_latin_digits

REMINDER_HINTS = ("یادم بنداز", "یادآوری", "یادآور", "آلارم", "remind")
FLIGHT_HINTS = ("بلیط", "بلیت", "پرواز", "تهران به", "به شیراز", "به مشهد", "flight")
BILL_HINTS = ("قبض برق", "قبض", "برق خونه", "برق خانه", "استعلام قبض")
INTERNET_HINTS = ("اینترنت", "بسته اینترنت", "adsl", "فیبر", "همراه اول", "ایرانسل")
SHOP_HINTS = ("بخر", "قیمت", "مقایسه کن", "ارزون", "ارزان")
SERVICE_HINTS = ("وقت بگیر", "نوبت", "تعویض روغن", "درخواست نوبت")
RESEARCH_HINTS = ("مقایسه", "پیدا کن", "جستجو", "کدوم شرکت")
MULTI_PASSENGER = ("دو بزرگسال", "دو نفر", "نوزاد", "infant", "کودک", "دو تا بلیط")
FORM_HINTS = ("این فرم", "سایتشون", "فرم سایت", "فرم وزارت", "سایت وزارت")

CITIES = {
    "تهران": "THR",
    "شیراز": "SYZ",
    "مشهد": "MHD",
    "اصفهان": "IFN",
    "تبریز": "TBZ",
    "کیش": "KIH",
    "اهواز": "AWZ",
    "یزد": "AZD",
}


def _split_intentions(text: str) -> list[str]:
    folded = fold_persian(text)
    # Split on independent task conjunctions without splitting "صبح باشه و زیر"
    parts = re.split(r"(?:\n+|؛|(?<!صبح باشه )\bبعد\b.+(?:هم|همچنین))", folded)
    # Also split "هم ... هم" style dual requests when both have verbs
    if " و " in folded:
        candidates = re.split(r"\s+و\s+(?=.*(?:یادم بنداز|بررسی کن|پیدا کن|وقت بگیر|مقایسه کن))", folded)
        if len(candidates) > 1:
            parts = candidates
    cleaned = [p.strip(" .،") for p in parts if p and p.strip()]
    return cleaned or [folded.strip()]


def _classify(chunk: str) -> IntentItem:
    folded = fold_persian(to_latin_digits(chunk))
    hard: dict = {}
    soft: dict = {}
    payload: dict = {}
    clarification = None
    kind = "personal"
    title = chunk[:80]

    if looks_like_otp_or_secret(chunk):
        return IntentItem(
            kind="secret_warning",
            title="هشدار رمز",
            original=chunk,
            needs_clarification="otp_in_chat",
        )

    if any(h in folded for h in REMINDER_HINTS):
        kind = "reminder"
        title = chunk
        if "هر روز" in folded or "روزانه" in folded:
            payload["recurrence"] = "daily"
        elif "هر هفته" in folded or "هفتگی" in folded:
            payload["recurrence"] = "weekly"
        else:
            payload["recurrence"] = "one_off"
        if "ساعت" not in folded and not re.search(r"\d{1,2}[:.]\d{2}", folded):
            payload["date_only"] = True
        payload["text"] = chunk

    elif any(h in folded for h in FLIGHT_HINTS):
        kind = "travel_search"
        title = "جستجوی پرواز داخلی"
        if any(h in folded for h in MULTI_PASSENGER):
            kind = "unsupported"
            clarification = "p0_one_adult_only"
            payload["unsupported_step"] = "رزرو چند مسافر / نوزاد خارج از محدودهٔ P0 است."
            payload["safe_partial"] = "جستجوی یک بزرگسال، یک‌طرفه، اکونومی"
        payload["one_way"] = True
        payload["cabin"] = "economy"
        payload["passengers"] = 1
        for name, code in CITIES.items():
            if f"{name} به" in folded or folded.startswith(name):
                payload.setdefault("origin", name)
                payload.setdefault("origin_code", code)
            if f"به {name}" in folded:
                payload["destination"] = name
                payload["destination_code"] = code
        if "صبح" in folded:
            if any(w in folded for w in ("ترجیحا", "ترجیحاً", "اگر بشه صبح")):
                soft["departure_window"] = "06:00-12:00"
                payload["morning_preference"] = True
            else:
                hard["departure_window"] = "06:00-12:00"
        money, money_q = parse_budget_phrase(folded)
        if money_q:
            clarification = money_q
        if money:
            hard["budget_amount"] = str(money.amount)
            hard["budget_unit"] = money.unit
        if "کد ملی" in folded or "شناسنامه" in folded:
            payload["note"] = "جستجوی عمومی نیاز به کد ملی ندارد."

    elif any(h in folded for h in BILL_HINTS):
        kind = "bill_inquiry"
        title = "استعلام قبض برق"
        payload["identifier_type"] = "bill_id_10"
        if "برق خانه" in folded or "برق خونه" in folded:
            payload["alias"] = "برق خانه"
        if "پرداخت" in folded or "پرداختش" in folded:
            payload["want_pay"] = True

    elif any(h in folded for h in INTERNET_HINTS):
        kind = "research"
        title = "مقایسه بسته اینترنت"
        payload["topic"] = "internet"
        if "ثابت" in folded or "adsl" in folded or "فیبر" in folded:
            payload["internet_kind"] = "fixed"
        elif "همراه" in folded or "موبایل" in folded:
            payload["internet_kind"] = "mobile"
        elif "همراه" not in folded and "موبایل" not in folded and "ثابت" not in folded and "adsl" not in folded and "فیبر" not in folded:
            clarification = "mobile_vs_fixed"
        if "ارزان‌ترین ایران" in folded or "ارزون‌ترین ایران" in folded:
            payload["forbid_national_cheapest_claim"] = True

    elif any(h in folded for h in SERVICE_HINTS) or (
        ("فرم" in folded and ("سایت" in folded or "بفرست" in folded or "وزارت" in folded))
        and "تعویض روغن" not in folded
    ):
        if "تعویض روغن" in folded or any(h in folded for h in ("وقت بگیر", "نوبت")):
            kind = "service_request"
            title = "درخواست خدمت محلی"
            payload["service"] = "oil_change" if "روغن" in folded else "local"
        else:
            kind = "unsupported"
            clarification = "arbitrary_form"
            payload["unsupported_step"] = "ارسال فرم دلخواه روی وب‌سایت پشتیبانی‌نشده"
            payload["safe_partial"] = "پیش‌نویس داخل برنامه یا تحویل به شما"
            title = "فرم پشتیبانی‌نشده"

    elif any(h in folded for h in SHOP_HINTS + RESEARCH_HINTS):
        kind = "research"
        title = "پژوهش و مقایسه"
        payload["topic"] = "shopping"
        if is_ambiguous_toman_phrase(folded) and "میلیون" not in folded:
            clarification = "expand_toman_amount"

    else:
        kind = "personal"
        title = chunk[:80]
        payload["text"] = chunk

    # Morning as hard when user said morning-only style for flights already handled.
    if kind == "travel_search" and "فقط صبح" in folded:
        hard["departure_window"] = "06:00-12:00"
        soft.pop("departure_window", None)

    return IntentItem(
        kind=kind,
        title=title,
        original=chunk,
        hard_constraints=hard,
        soft_preferences=soft,
        needs_clarification=clarification,
        payload=payload,
    )


def extract_intents(text: str) -> IntentResult:
    secret = looks_like_otp_or_secret(text)
    if secret and re.search(r"\b\d{4,8}\b", to_latin_digits(text)):
        return IntentResult(
            items=[
                IntentItem(
                    kind="secret_warning",
                    title="رمز در گفتگو",
                    original=text,
                    needs_clarification="otp_in_chat",
                )
            ],
            secret_detected=True,
        )
    chunks = _split_intentions(text)
    items = [_classify(c) for c in chunks]
    if len(items) > 3:
        return IntentResult(
            items=items[:3],
            batch_proposal=True,
            leftover=[i.original for i in items[3:]],
        )
    return IntentResult(items=items, secret_detected=False)
