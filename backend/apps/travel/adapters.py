from datetime import UTC, datetime, time
from decimal import Decimal

from apps.core.money import quote_from_provider

RETRIEVED = datetime(2026, 9, 17, 7, 30, tzinfo=UTC)


def _offer(source: str, **kwargs) -> dict:
    kwargs.setdefault("sandbox", True)
    kwargs.setdefault("sandbox_label_fa", "آزمایشی")
    kwargs.setdefault("retrieved_at", RETRIEVED.isoformat())
    kwargs.setdefault("timezone", "Asia/Tehran")
    kwargs.setdefault("cabin", "economy")
    kwargs.setdefault("passengers", 1)
    kwargs.setdefault("availability_caveat_fa", "موجودی آزمایشی است و تضمین رزرو نیست.")
    return {"source_slug": source, **kwargs}


ALPHA_OFFERS = [
    _offer(
        "flight_search_alpha",
        id="alpha-thr-syz-1",
        provider_name_fa="منبع آلفا (آزمایشی)",
        carrier="Sandbox Air",
        origin="تهران",
        destination="شیراز",
        origin_code="THR",
        destination_code="SYZ",
        date="2026-09-18",
        depart_time="08:15",
        arrive_time="09:35",
        baggage_fa="۲۰ کیلو",
        amount="4200000",
        unit="toman",
        fees=[{"label_fa": "عوارض فرودگاهی", "amount": "180000", "unit": "toman"}],
        restrictions_fa="غیرقابل استرداد در سندباکس",
        handoff_url="https://sandbox.yavar.local/alpha/offer/alpha-thr-syz-1",
        preserves_offer=True,
    ),
    _offer(
        "flight_search_alpha",
        id="alpha-thr-syz-2",
        provider_name_fa="منبع آلفا (آزمایشی)",
        carrier="Sandbox Air",
        origin="تهران",
        destination="شیراز",
        origin_code="THR",
        destination_code="SYZ",
        date="2026-09-18",
        depart_time="16:40",
        arrive_time="18:00",
        baggage_fa="۲۰ کیلو",
        amount="3900000",
        unit="toman",
        fees=[{"label_fa": "عوارض فرودگاهی", "amount": "180000", "unit": "toman"}],
        restrictions_fa="",
        handoff_url="https://sandbox.yavar.local/alpha/offer/alpha-thr-syz-2",
        preserves_offer=True,
    ),
    _offer(
        "flight_search_alpha",
        id="alpha-thr-syz-expensive",
        provider_name_fa="منبع آلفا (آزمایشی)",
        carrier="Sandbox Air",
        origin="تهران",
        destination="شیراز",
        date="2026-09-18",
        depart_time="09:00",
        arrive_time="10:20",
        amount="7200000",
        unit="toman",
        fees=[{"label_fa": "عوارض", "amount": "200000", "unit": "toman"}],
        handoff_url="https://sandbox.yavar.local/alpha/offer/expensive",
        preserves_offer=True,
    ),
]

BETA_OFFERS = [
    _offer(
        "flight_search_beta",
        id="beta-thr-syz-1",
        provider_name_fa="منبع بتا (آزمایشی)",
        carrier="Beta Sandbox",
        origin="تهران",
        destination="شیراز",
        date="2026-09-18",
        depart_time="07:50",
        arrive_time="09:10",
        amount="4500000",
        unit="toman",
        fees=[{"label_fa": "کارمزد خدمات", "amount": "50000", "unit": "toman"}],
        handoff_url="https://sandbox.yavar.local/beta/search?from=THR&to=SYZ",
        preserves_offer=False,
    ),
]

PRICE_CHANGE = {
    "alpha-thr-syz-1": _offer(
        "flight_search_alpha",
        id="alpha-thr-syz-1",
        provider_name_fa="منبع آلفا (آزمایشی)",
        carrier="Sandbox Air",
        origin="تهران",
        destination="شیراز",
        date="2026-09-18",
        depart_time="08:15",
        arrive_time="09:35",
        amount="4650000",
        unit="toman",
        fees=[{"label_fa": "عوارض فرودگاهی", "amount": "180000", "unit": "toman"}],
        handoff_url="https://sandbox.yavar.local/alpha/offer/alpha-thr-syz-1",
        preserves_offer=True,
        price_changed=True,
    )
}

_alpha_down = False
_force_price_change = False


def set_alpha_down(value: bool) -> None:
    global _alpha_down
    _alpha_down = value


def set_price_change(value: bool) -> None:
    global _force_price_change
    _force_price_change = value


def _in_morning(depart: str) -> bool:
    h, m = map(int, depart.split(":"))
    t = time(h, m)
    return time(6, 0) <= t < time(12, 0)


def search(*, origin: str, destination: str, hard: dict, soft: dict, sources: list[str] | None = None) -> dict:
    sources = sources or ["flight_search_alpha", "flight_search_beta"]
    missing = []
    collected: list[dict] = []
    if "flight_search_alpha" in sources:
        if _alpha_down:
            missing.append({"slug": "flight_search_alpha", "name_fa": "منبع آلفا (آزمایشی)"})
        else:
            collected.extend(ALPHA_OFFERS)
    if "flight_search_beta" in sources:
        collected.extend(BETA_OFFERS)

    budget = None
    if hard.get("budget_amount"):
        budget = quote_from_provider(amount=hard["budget_amount"], unit=hard.get("budget_unit", "toman"))
    window = hard.get("departure_window")
    matches, near = [], []
    for off in collected:
        if origin and off.get("origin") not in {origin, origin[:3]} and origin not in off.get("origin", ""):
            if origin not in (off.get("origin"), off.get("origin_code")):
                continue
        violated = None
        total = Decimal(off["amount"])
        for fee in off.get("fees") or []:
            if fee.get("amount"):
                total += Decimal(fee["amount"])
        if budget and total > budget.amount:
            violated = "بودجه"
        if window == "06:00-12:00" and not _in_morning(off["depart_time"]):
            violated = violated or "پنجرهٔ صبح"
        row = {**off, "total_with_known_fees": str(total), "is_match": violated is None, "violated_constraint": violated or ""}
        if violated:
            near.append(row)
        else:
            matches.append(row)
    return {
        "sandbox": True,
        "partial": bool(missing),
        "missing_sources": missing,
        "matches": matches,
        "near_matches": near,
        "disclaimer_fa": "نتایج آزمایشی است؛ ارزان‌ترین ایران ادعا نمی‌شود.",
    }


def recheck(offer_id: str) -> dict:
    if _force_price_change and offer_id in PRICE_CHANGE:
        return PRICE_CHANGE[offer_id]
    for pool in (ALPHA_OFFERS, BETA_OFFERS):
        for off in pool:
            if off["id"] == offer_id:
                return off
    raise KeyError(offer_id)
