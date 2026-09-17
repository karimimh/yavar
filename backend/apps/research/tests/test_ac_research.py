import pytest

from apps.agent.runtime import process_message
from apps.core.enums import ExecutionState
from apps.core.money import UnusableQuoteError
from apps.research.adapters import INJECTION_PAGE, compare, validate_quote
from apps.tasks.models import Task


@pytest.mark.django_db
def test_ac14_internet_clarify(user):
    result = process_message(user, "این ماه اینترنت کدوم شرکت برای من ارزون‌تره؟ مقایسه کن.")
    task = Task.objects.get(id=result["tasks"][0]["id"])
    assert task.execution_state == ExecutionState.NEEDS_INFORMATION
    assert "همراه" in (task.current_activity_fa or "") or "ثابت" in (task.current_activity_fa or "")


@pytest.mark.django_db
def test_ac15_unverified_coverage(user, auth_client):
    result = process_message(user, "اینترنت ثابت مقایسه کن")
    task = Task.objects.get(id=result["tasks"][0]["id"])
    # may still need mobile_vs_fixed if wording didn't include ثابت as type... "اینترنت ثابت" has ثابت
    if task.execution_state == ExecutionState.NEEDS_INFORMATION:
        r = auth_client.post(
            f"/api/tasks/{task.id}/clarify/",
            {"internet_kind": "fixed", "topic": "internet"},
            content_type="application/json",
        )
        assert r.status_code == 200
        task.refresh_from_db()
    offers = list(task.offers.all())
    if offers:
        assert any("coverage" in (o.unverified_fields or []) or "address_eligibility" in (o.unverified_fields or []) for o in offers)


def test_ac16_unlike_variants_not_identical():
    result = compare(topic="shopping", constraints={})
    capacities = {tuple(sorted((o.get("attributes") or {}).items())) for o in result["options"]}
    assert len(result["options"]) >= 2
    assert len(capacities) >= 2


def test_ac17_missing_unit_unusable():
    bad = {"amount": "5000000", "unit": None, "unusable": True}
    try:
        validate_quote(bad)
        raise AssertionError("must be unusable")
    except UnusableQuoteError:
        pass
    result = compare(topic="shopping", constraints={})
    assert result["unusable_quotes"]


@pytest.mark.django_db
def test_ac18_five_toman_asks(user):
    result = process_message(user, "این هدفون را پنج تومن بخر مقایسه کن")
    task = Task.objects.get(id=result["tasks"][0]["id"])
    assert task.execution_state == ExecutionState.NEEDS_INFORMATION


def test_ac36_injection_ignored():
    result = compare(topic="shopping", constraints={"include_untrusted": True})
    assert result["untrusted_excerpt_example"] == INJECTION_PAGE
    assert "attacker" in (result["untrusted_excerpt_example"] or "")
    # no authorization side effect fields
    assert "grant approval" not in str(result.get("options"))
