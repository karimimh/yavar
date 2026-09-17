from apps.agent.intent import extract_intents


def test_persian_colloquial_reminder() -> None:
    result = extract_intents("فردا ساعت ۱۰ یادم بنداز قبض رو بررسی کنم")
    assert len(result.items) == 1
    assert result.items[0].kind == "reminder"


def test_hard_budget_vs_soft_morning_preference() -> None:
    result = extract_intents("بلیط تهران به شیراز ترجیحا صبح و زیر ۵ میلیون")
    item = result.items[0]
    assert item.kind == "travel_search"
    assert "budget_amount" in item.hard_constraints
    assert item.soft_preferences.get("departure_window") == "06:00-12:00"


def test_morning_requirement_is_hard() -> None:
    result = extract_intents("برای پنجشنبه یه بلیط تهران به شیراز پیدا کن، صبح باشه و زیر ۵ میلیون")
    item = result.items[0]
    assert item.hard_constraints.get("departure_window") == "06:00-12:00"
    assert item.hard_constraints.get("budget_amount") == "5000000"


def test_three_intention_cap() -> None:
    text = (
        "یادم بنداز فردا ساعت ۱۰ قبض "
        "و بلیط تهران به شیراز پیدا کن "
        "و اینترنت همراه مقایسه کن "
        "و تعویض روغن وقت بگیر"
    )
    result = extract_intents(text)
    assert result.batch_proposal or len(result.items) <= 3


def test_otp_in_chat_flagged() -> None:
    result = extract_intents("کد تأیید 445566")
    assert result.secret_detected
