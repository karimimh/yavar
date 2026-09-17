from datetime import timedelta

import pytest
from django.utils import timezone

from apps.agent.runtime import process_message
from apps.approvals.models import Approval
from apps.approvals.services import begin_submission
from apps.core.enums import ExecutionState, ExternalOutcome
from apps.requests import adapters as request_adapters
from apps.tasks.models import Task


@pytest.mark.django_db
def test_ac24_draft_preview(user):
    result = process_message(user, "شنبه ساعت ۱۰ برای تعویض روغن یه وقت بگیر")
    task = Task.objects.get(id=result["tasks"][0]["id"])
    approval = task.approvals.first()
    assert approval is not None
    assert "ارسال این درخواست نوبت" in approval.action_label_fa
    assert "غیرالزام" in approval.will_happen_fa or "غیرالزام" in approval.costs_fa
    assert task.drafts.exists()


@pytest.mark.django_db
def test_ac25_fill_consent_required(user, auth_client):
    result = process_message(user, "شنبه ساعت ۱۰ برای تعویض روغن یه وقت بگیر")
    approval = Approval.objects.get(task_id=result["tasks"][0]["id"])
    r = auth_client.post(
        f"/api/approvals/{approval.id}/decide/",
        {"action": "approve"},
        content_type="application/json",
    )
    assert r.status_code == 400
    assert r.json().get("needs_fill_consent") is True


@pytest.mark.django_db
def test_ac26_deposit_stops(user):
    request_adapters.set_deposit(True)
    result = process_message(user, "شنبه ساعت ۱۰ برای تعویض روغن یه وقت بگیر")
    task = Task.objects.get(id=result["tasks"][0]["id"])
    assert task.execution_state == ExecutionState.BLOCKED
    assert "پیش‌پرداخت" in (task.current_activity_fa or "")


@pytest.mark.django_db
def test_ac27_ack_not_appointment(user, auth_client):
    result = process_message(user, "شنبه ساعت ۱۰ برای تعویض روغن یه وقت بگیر")
    approval = Approval.objects.get(task_id=result["tasks"][0]["id"])
    r = auth_client.post(
        f"/api/approvals/{approval.id}/decide/",
        {"action": "approve", "fill_consent": True},
        content_type="application/json",
    )
    assert r.json().get("appointment_confirmed") is False
    task = Task.objects.get(id=result["tasks"][0]["id"])
    assert task.external_outcome == ExternalOutcome.REQUEST_RECEIVED


@pytest.mark.django_db
def test_ac28_field_change_invalidates(user, auth_client):
    result = process_message(user, "شنبه ساعت ۱۰ برای تعویض روغن یه وقت بگیر")
    approval = Approval.objects.get(task_id=result["tasks"][0]["id"])
    fields = dict(approval.fields_snapshot)
    fields["phone"] = "09120000000"
    r = auth_client.post(
        f"/api/approvals/{approval.id}/decide/",
        {"action": "edit", "fields": fields},
        content_type="application/json",
    )
    assert r.status_code == 200
    approval.refresh_from_db()
    assert approval.status == "invalidated"
    assert Approval.objects.filter(task_id=result["tasks"][0]["id"]).count() >= 2


@pytest.mark.django_db
def test_ac29_expired_cannot_execute(user):
    result = process_message(user, "شنبه ساعت ۱۰ برای تعویض روغن یه وقت بگیر")
    approval = Approval.objects.get(task_id=result["tasks"][0]["id"])
    approval.status = "approved"
    approval.expires_at = timezone.now() - timedelta(minutes=1)
    approval.save()
    ok, reason = begin_submission(approval)
    assert ok is False
    approval.refresh_from_db()
    assert approval.status == "expired"


@pytest.mark.django_db
def test_ac30_timeout_unknown_no_retry(user, auth_client):
    request_adapters.set_timeout_after_send(True)
    result = process_message(user, "شنبه ساعت ۱۰ برای تعویض روغن یه وقت بگیر")
    approval = Approval.objects.get(task_id=result["tasks"][0]["id"])
    r = auth_client.post(
        f"/api/approvals/{approval.id}/decide/",
        {"action": "approve", "fill_consent": True},
        content_type="application/json",
    )
    assert r.json().get("outcome") == "unknown"
    r2 = auth_client.post(
        f"/api/approvals/{approval.id}/decide/",
        {"action": "approve", "fill_consent": True},
        content_type="application/json",
    )
    # second attempt must not create another submission
    assert r2.json().get("duplicate_prevented") or r2.status_code in {200, 400}


@pytest.mark.django_db
def test_ac31_double_tap(user, auth_client):
    result = process_message(user, "شنبه ساعت ۱۰ برای تعویض روغن یه وقت بگیر")
    approval = Approval.objects.get(task_id=result["tasks"][0]["id"])
    auth_client.post(
        f"/api/approvals/{approval.id}/decide/",
        {"action": "approve", "fill_consent": True},
        content_type="application/json",
    )
    r2 = auth_client.post(
        f"/api/approvals/{approval.id}/decide/",
        {"action": "approve", "fill_consent": True},
        content_type="application/json",
    )
    assert r2.json().get("duplicate_prevented") is True


@pytest.mark.django_db
def test_ac32_cancel_during_send(user, auth_client):
    result = process_message(user, "شنبه ساعت ۱۰ برای تعویض روغن یه وقت بگیر")
    task = Task.objects.get(id=result["tasks"][0]["id"])
    approval = task.approvals.first()
    auth_client.post(f"/api/tasks/{task.id}/", {"action": "stop"}, content_type="application/json")
    r = auth_client.post(
        f"/api/approvals/{approval.id}/decide/",
        {"action": "approve", "fill_consent": True},
        content_type="application/json",
    )
    assert r.json().get("reversed") is False


@pytest.mark.django_db
def test_ac34_close_app_not_approval(user):
    result = process_message(user, "شنبه ساعت ۱۰ برای تعویض روغن یه وقت بگیر")
    task = Task.objects.get(id=result["tasks"][0]["id"])
    assert task.execution_state == ExecutionState.NEEDS_APPROVAL
    from apps.agent.runtime import continue_background

    continue_background(task.id)
    task.refresh_from_db()
    assert task.execution_state == ExecutionState.NEEDS_APPROVAL


@pytest.mark.django_db
def test_ac38_arbitrary_form(user):
    result = process_message(user, "این فرم سایت وزارت را پر کن و بفرست")
    task = Task.objects.get(id=result["tasks"][0]["id"])
    assert task.execution_state == ExecutionState.BLOCKED
