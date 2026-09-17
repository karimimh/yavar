"""Persian digit, phone, and mixed-script helpers. Spec 13.1 / 13.4."""

from __future__ import annotations

import re
import unicodedata

PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
LATIN_DIGITS = "0123456789"

_PERSIAN_TO_LATIN = str.maketrans(PERSIAN_DIGITS, LATIN_DIGITS)
_ARABIC_TO_LATIN = str.maketrans(ARABIC_DIGITS, LATIN_DIGITS)
_LATIN_TO_PERSIAN = str.maketrans(LATIN_DIGITS, PERSIAN_DIGITS)

# Common Persian colloquial / Arabic-Persian letter variants.
_LETTER_FOLD = str.maketrans(
    {
        "ي": "ی",
        "ك": "ک",
        "ة": "ه",
        "ؤ": "و",
        "إ": "ا",
        "أ": "ا",
        "ٱ": "ا",
    }
)

OTP_PATTERN = re.compile(
    r"(?:رمز|otp|کد\s*تأیید|کد\s*تایید|کد\s*یکبارمصرف|verification\s*code)"
    r"|(\b\d{4,8}\b)",
    re.IGNORECASE,
)

SECRET_HINT_PATTERN = re.compile(
    r"(رمز\s*یکبارمصرف|کد\s*تأیید|کد\s*تایید|\botp\b|cvv|cvv2|شماره\s*کارت|کارت\s*بانک)",
    re.IGNORECASE,
)


def to_latin_digits(value: str) -> str:
    return value.translate(_ARABIC_TO_LATIN).translate(_PERSIAN_TO_LATIN)


def to_persian_digits(value: str) -> str:
    return to_latin_digits(value).translate(_LATIN_TO_PERSIAN)


def fold_persian(value: str) -> str:
    """Normalize Arabic/Persian letter variants and half-spaces without destroying copy values."""
    text = unicodedata.normalize("NFKC", value)
    text = text.translate(_LETTER_FOLD)
    text = text.replace("\u200c", " ").replace("\u200d", "")
    return text


def looks_like_otp_or_secret(text: str) -> bool:
    folded = fold_persian(to_latin_digits(text))
    if SECRET_HINT_PATTERN.search(folded):
        return True
    # A standalone 4–8 digit token with verification wording nearby.
    if re.search(r"(رمز|کد|otp)", folded, re.IGNORECASE) and re.search(r"\b\d{4,8}\b", folded):
        return True
    return False


def extract_secret_spans(text: str) -> list[str]:
    folded = to_latin_digits(text)
    return re.findall(r"\b\d{4,8}\b", folded)


def normalize_phone(raw: str) -> tuple[str, str]:
    """Return (canonical E.164-like Iranian number, original trimmed input).

    Canonical form for Iranian mobiles: +989XXXXXXXXX. Original is preserved separately.
    """
    original = raw.strip()
    digits = re.sub(r"[^\d+]", "", to_latin_digits(original))
    if digits.startswith("+"):
        digits = "+" + re.sub(r"\D", "", digits)
    else:
        digits = re.sub(r"\D", "", digits)

    body = digits.lstrip("+")
    if body.startswith("0098"):
        body = body[4:]
    elif body.startswith("98"):
        body = body[2:]
    elif body.startswith("0"):
        body = body[1:]

    if len(body) == 10 and body.startswith("9"):
        return f"+98{body}", original
    if len(body) == 10:
        # Still store as +98 for Iranian P0; format validity is not identity proof.
        return f"+98{body}", original
    raise ValueError("شماره موبایل نامعتبر است.")
