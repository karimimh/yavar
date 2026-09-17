import pytest

from apps.agent.runtime import process_message
from apps.bills import adapters as bill_adapters
from apps.core.enums import ExecutionState, ExternalOutcome
from apps.memory.models import SavedFact
from apps.tasks.models import Task


@pytest.mark.django_db
def test_ac19_alias_requires_consent(user):
    SavedFact.objects.create(
        user=user, kind="bill_alias", label="برق خانه", value="THRHOME01", origin_fa="کاربر"
    )
    result = process_message(user, "قبض برق خانه رو بررسی کن")
    task = Task.objects.get(id=result["tasks"][0]["id"])
    assert task.execution_state == ExecutionState.NEEDS_INFORMATION
    assert "رضایت" in (task.current_activity_fa or "")


@pytest.mark.django_db
def test_ac19_consent_then_inquire(user, auth_client):
    SavedFact.objects.create(
        user=user, kind="bill_alias", label="برق خانه", value="THRHOME01", origin_fa="کاربر"
    )
    result = process_message(user, "قبض برق خانه رو بررسی کن")
    task = Task.objects.get(id=result["tasks"][0]["id"])
    r = auth_client.post(
        f"/api/tasks/{task.id}/clarify/",
        {"disclosure_consent": True, "alias": "برق خانه"},
        content_type="application/json",
    )
    assert r.status_code == 200
    task.refresh_from_db()
    assert task.payload.get("data_origin") == "checked_with_provider"
    assert task.external_outcome == ExternalOutcome.PREPARED_ONLY


@pytest.mark.django_db
def test_ac20_live_fail_does_not_claim_screenshot(user, auth_client):
    SavedFact.objects.create(
        user=user, kind="bill_alias", label="برق خانه", value="THRHOME01", origin_fa="کاربر"
    )
    bill_adapters.set_live_fail(True)
    result = process_message(user, "قبض برق خانه رو بررسی کن")
    task = Task.objects.get(id=result["tasks"][0]["id"])
    auth_client.post(
        f"/api/tasks/{task.id}/clarify/",
        {"disclosure_consent": True, "alias": "برق خانه"},
        content_type="application/json",
    )
    task.refresh_from_db()
    assert task.execution_state == ExecutionState.FAILED
    assert "تصویر" in (task.current_activity_fa or "")


@pytest.mark.django_db
def test_ac21_return_not_paid(user, auth_client):
    SavedFact.objects.create(
        user=user, kind="bill_alias", label="برق خانه", value="THRHOME01", origin_fa="کاربر"
    )
    result = process_message(user, "قبض برق خانه رو بررسی کن")
    task = Task.objects.get(id=result["tasks"][0]["id"])
    auth_client.post(
        f"/api/tasks/{task.id}/clarify/",
        {"disclosure_consent": True, "alias": "برق خانه"},
        content_type="application/json",
    )
    auth_client.post(f"/api/bills/tasks/{task.id}/pay/", {}, content_type="application/json")
    r = auth_client.post(f"/api/bills/tasks/{task.id}/pay/return/", {}, content_type="application/json")
    assert r.json()["paid"] is False
    assert r.json()["verified"] is False


@pytest.mark.django_db
def test_ac22_user_reported_paid(user, auth_client):
    result = process_message(user, "فردا ساعت ۱۰ یادم بنداز قبض")
    task_id = result["tasks"][0]["id"]
    r = auth_client.post(
        f"/api/tasks/{task_id}/",
        {"action": "user_paid"},
        content_type="application/json",
    )
    assert r.json()["external_outcome"] == "user_reported_complete"


@pytest.mark.django_db
def test_ac23_otp_in_chat(user):
    result = process_message(user, "کد تأیید 112233")
    assert result["secret_warning"] is True
    assert result["offer_delete"] is True
    assert Task.objects.filter(user=user).count() == 0


@pytest.mark.django_db
def test_ac37_unexpected_payment_domain(user, auth_client):
    SavedFact.objects.create(
        user=user, kind="bill_alias", label="برق خانه", value="THRHOME01", origin_fa="کاربر"
    )
    result = process_message(user, "قبض برق خانه رو بررسی کن")
    task = Task.objects.get(id=result["tasks"][0]["id"])
    auth_client.post(
        f"/api/tasks/{task.id}/clarify/",
        {"disclosure_consent": True, "alias": "برق خانه"},
        content_type="application/json",
    )
    bill_adapters.set_unexpected_redirect(True)
    r = auth_client.post(f"/api/bills/tasks/{task.id}/pay/", {}, content_type="application/json")
    assert r.status_code == 409
    task.refresh_from_db()
    assert task.execution_state == ExecutionState.NEEDS_USER_TAKEOVER
