"""Money helpers. Never infer unit from magnitude. Spec 13.3, QUAL-04."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from apps.core.enums import MoneyUnit
from apps.core.persian import fold_persian, to_latin_digits

RIALS_PER_TOMAN = Decimal(10)

_AMOUNT_RE = re.compile(
    r"(\d[\d,]*(?:\.\d+)?)\s*(تومان|تومن|ریال|rial|toman)?",
    re.IGNORECASE,
)

_AMBIGUOUS_TOMAN = re.compile(r"(پنج\s*تومن|چند\s*تومن|\d+\s*تومن)")


@dataclass(frozen=True)
class Money:
    amount: Decimal
    unit: str
    original_amount: Decimal | None = None
    original_unit: str | None = None
    display_toman: Decimal | None = None

    def as_dict(self) -> dict:
        return {
            "amount": str(self.amount),
            "unit": self.unit,
            "original_amount": str(self.original_amount) if self.original_amount is not None else None,
            "original_unit": self.original_unit,
            "display_toman": str(self.display_toman) if self.display_toman is not None else None,
        }


class UnusableQuoteError(ValueError):
    """Quote cannot be used for a consequential comparison."""


class AmbiguousAmountError(ValueError):
    """User amount needs clarification before a purchase/handoff."""


def parse_decimal(raw: str) -> Decimal:
    text = to_latin_digits(raw).replace(",", "").replace("٬", "").replace("،", "").strip()
    try:
        return Decimal(text)
    except InvalidOperation as exc:
        raise ValueError("مقدار عددی نامعتبر است.") from exc


def convert_known_denomination(amount: Decimal, unit: str) -> Money:
    """Convert rial↔toman only when the provider denomination is known."""
    unit = unit.lower()
    if unit == MoneyUnit.RIAL:
        toman = amount / RIALS_PER_TOMAN
        return Money(
            amount=amount,
            unit=MoneyUnit.RIAL,
            original_amount=amount,
            original_unit=MoneyUnit.RIAL,
            display_toman=toman,
        )
    if unit == MoneyUnit.TOMAN:
        return Money(
            amount=amount,
            unit=MoneyUnit.TOMAN,
            original_amount=amount,
            original_unit=MoneyUnit.TOMAN,
            display_toman=amount,
        )
    raise UnusableQuoteError("واحد پول مشخص نیست؛ از روی بزرگی عدد حدس زده نمی‌شود.")


def quote_from_provider(*, amount: Decimal | str | int | None, unit: str | None) -> Money:
    if amount is None or unit in (None, "", MoneyUnit.UNKNOWN):
        raise UnusableQuoteError("نقل‌قول بدون واحد برای مقایسهٔ مالی قابل استفاده نیست.")
    if isinstance(amount, str):
        amount = parse_decimal(amount)
    elif isinstance(amount, int):
        amount = Decimal(amount)
    return convert_known_denomination(Decimal(amount), unit)


def is_ambiguous_toman_phrase(text: str) -> bool:
    folded = fold_persian(to_latin_digits(text))
    if "پنج تومن" in folded or "پنج‌تومن" in folded.replace(" ", ""):
        return True
    return bool(_AMBIGUOUS_TOMAN.search(folded))


def parse_budget_phrase(text: str) -> tuple[Money | None, str | None]:
    """Return (money, clarification_reason). clarification_reason set when user must confirm."""
    folded = fold_persian(to_latin_digits(text))
    if is_ambiguous_toman_phrase(folded) and "میلیون" not in folded:
        return None, "پنج تومن در بافت خرید مبهم است؛ مبلغ کامل و واحد را مشخص کنید."

    million = re.search(r"(زیر|تا|حداکثر)?\s*(\d+)\s*میلیون", folded)
    if million:
        n = Decimal(million.group(2)) * Decimal(1_000_000)
        return Money(amount=n, unit=MoneyUnit.TOMAN, original_amount=n, original_unit=MoneyUnit.TOMAN, display_toman=n), None

    match = _AMOUNT_RE.search(folded.replace("٬", ","))
    if not match:
        return None, None
    raw_amount, unit_word = match.group(1), (match.group(2) or "").lower()
    amount = parse_decimal(raw_amount)
    if unit_word in {"تومان", "تومن", "toman"}:
        if amount <= 20 and "میلیون" not in folded:
            return None, "مبلغ کوتاه با واحد «تومن» مبهم است؛ مقدار کامل را بنویسید."
        return convert_known_denomination(amount, MoneyUnit.TOMAN), None
    if unit_word in {"ریال", "rial"}:
        return convert_known_denomination(amount, MoneyUnit.RIAL), None
    return None, None


def format_money_fa(money: Money) -> str:
    amount = money.display_toman if money.display_toman is not None else money.amount
    quantized = f"{amount:,.0f}".replace(",", "٬")
    from apps.core.persian import to_persian_digits

    unit = "تومان" if money.unit in {MoneyUnit.TOMAN, MoneyUnit.RIAL} else "نامشخص"
    if money.unit == MoneyUnit.RIAL:
        return f"{to_persian_digits(quantized)} تومان (اصل: {to_persian_digits(str(money.amount))} ریال)"
    return f"{to_persian_digits(quantized)} {unit}"
