from datetime import datetime
from zoneinfo import ZoneInfo

from apps.core.dates import resolve_relative_date
from apps.core.money import (
    UnusableQuoteError,
    is_ambiguous_toman_phrase,
    parse_budget_phrase,
    quote_from_provider,
)
from apps.core.persian import looks_like_otp_or_secret, normalize_phone, to_latin_digits


def test_persian_digits_and_phone() -> None:
    assert to_latin_digits("۰۹۱۲") == "0912"
    phone, original = normalize_phone("۰۹۱۲۱۱۱۱۱۱۱")
    assert phone == "+989121111111"
    assert original == "۰۹۱۲۱۱۱۱۱۱۱"


def test_otp_detection() -> None:
    assert looks_like_otp_or_secret("کد تأیید 123456")
    assert looks_like_otp_or_secret("OTP 998877")
    assert not looks_like_otp_or_secret("فردا ساعت ۱۰ یادم بنداز")


def test_never_infer_unit_from_magnitude() -> None:
    try:
        quote_from_provider(amount="5000000", unit=None)
        raise AssertionError("should fail")
    except UnusableQuoteError:
        pass


def test_rial_toman_only_when_known() -> None:
    m = quote_from_provider(amount="10", unit="rial")
    assert m.display_toman == 1


def test_five_toman_ambiguous() -> None:
    assert is_ambiguous_toman_phrase("این را پنج تومن بخر")
    money, q = parse_budget_phrase("زیر ۵ میلیون")
    assert money is not None
    assert money.amount == 5_000_000


def test_ambiguous_thursday() -> None:
    # 17 Sep 2026 is Thursday
    now = datetime(2026, 9, 17, 12, 0, tzinfo=ZoneInfo("Asia/Tehran"))
    resolved = resolve_relative_date("پنجشنبه یادم بنداز", timezone="Asia/Tehran", now=now)
    assert resolved is not None
    assert resolved.ambiguous
