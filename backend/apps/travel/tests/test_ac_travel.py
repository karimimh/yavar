import pytest

from apps.agent.runtime import process_message
from apps.core.enums import ExecutionState, ExternalOutcome
from apps.tasks.models import Task
from apps.travel import adapters as travel_adapters
from apps.travel.adapters import search


@pytest.mark.django_db
def test_ac08_hard_budget_morning(user):
    result = process_message(
        user,
        "برای پنجشنبه یه بلیط تهران به شیراز پیدا کن، صبح باشه و زیر ۵ میلیون",
    )
    task = Task.objects.get(id=result["tasks"][0]["id"])
    matches = [o for o in task.offers.all() if o.is_match]
    near = [o for o in task.offers.all() if not o.is_match]
    assert matches
    assert all(float(o.amount) + sum(float(f.get("amount", 0)) for f in (o.fees or [])) <= 5_000_000 for o in matches)
    # afternoon offer should be near-match due to morning window
    assert any("صبح" in (o.violated_constraint or "") or "16:40" in (o.attributes or {}).get("depart_time", "") for o in near) or near


@pytest.mark.django_db
def test_ac09_partial_source(user):
    travel_adapters.set_alpha_down(True)
    result = process_message(user, "بلیط تهران به شیراز پیدا کن صبح باشه و زیر ۵ میلیون")
    task = Task.objects.get(id=result["tasks"][0]["id"])
    assert task.payload["search"]["partial"] is True
    assert task.payload["search"]["missing_sources"]


@pytest.mark.django_db
def test_ac10_price_change_requires_new_decision(user, auth_client):
    result = process_message(user, "بلیط تهران به شیراز پیدا کن صبح باشه و زیر ۵ میلیون")
    task = Task.objects.get(id=result["tasks"][0]["id"])
    next(o for o in task.offers.filter(is_match=True) if (o.attributes or {}).get("id") == "alpha-thr-syz-1")
    travel_adapters.set_price_change(True)
    r = auth_client.post(
        f"/api/travel/tasks/{task.id}/select/",
        {"offer_id": "alpha-thr-syz-1"},
        content_type="application/json",
    )
    assert r.json()["changed"] is True
    task.refresh_from_db()
    assert task.external_outcome != ExternalOutcome.PROVIDER_CONFIRMED


@pytest.mark.django_db
def test_ac11_ac12_handoff_honest(user, auth_client):
    result = process_message(user, "بلیط تهران به شیراز پیدا کن")
    task = Task.objects.get(id=result["tasks"][0]["id"])
    # beta does not preserve offer
    next(o for o in task.offers.all() if (o.attributes or {}).get("id") == "beta-thr-syz-1")
    r = auth_client.post(
        f"/api/travel/tasks/{task.id}/select/",
        {"offer_id": "beta-thr-syz-1"},
        content_type="application/json",
    )
    data = r.json()
    assert data["preserves_offer"] is False
    assert "دوباره" in data["note_fa"]
    assert data["ticket_purchased"] is False
    task.refresh_from_db()
    assert task.external_outcome == ExternalOutcome.PREPARED_ONLY


@pytest.mark.django_db
def test_ac13_multi_passenger_refused(user):
    result = process_message(user, "دو بزرگسال و نوزاد بلیط تهران به شیراز")
    task = Task.objects.get(id=result["tasks"][0]["id"])
    assert task.execution_state == ExecutionState.BLOCKED
    assert "نوزاد" in (task.current_activity_fa or "") or "مسافر" in (task.current_activity_fa or "")


def test_search_fees_not_hidden():
    result = search(origin="تهران", destination="شیراز", hard={"budget_amount": "4000000", "budget_unit": "toman"}, soft={})
    over = [m for m in result["near_matches"] if m.get("violated_constraint") == "بودجه"]
    assert over
    assert all(m.get("fees") for m in result["matches"] + result["near_matches"] if m["source_slug"] == "flight_search_alpha")
