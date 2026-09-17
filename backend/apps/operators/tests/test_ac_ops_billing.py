import pytest

from apps.agent.runtime import continue_background, process_message
from apps.billing.models import SubscriptionPayment
from apps.billing.services import remaining_runs, reserve_run, restore_run, serialize_entitlement
from apps.core.enums import ExecutionState, ExternalOutcome, TaskKind
from apps.coverage.models import Capability
from apps.tasks.models import Task


@pytest.mark.django_db
def test_ac33_background_research(user):
    result = process_message(user, "هدفون مدل X مقایسه کن")
    task = Task.objects.get(id=result["tasks"][0]["id"])
    # already delivered synchronously; simulate queued public search
    task.execution_state = ExecutionState.IN_PROGRESS
    task.kind = TaskKind.RESEARCH
    task.save()
    continue_background(task.id)
    task.refresh_from_db()
    assert task.execution_state == ExecutionState.DELIVERED


@pytest.mark.django_db
def test_ac35_partial_three_tasks(user):
    from apps.bills import adapters as bill_adapters

    bill_adapters.set_live_fail(True)
    # three independent intents
    r1 = process_message(user, "فردا ساعت ۱۰ یادم بنداز دارو")
    r2 = process_message(user, "هدفون مدل X مقایسه کن")
    from apps.memory.models import SavedFact

    SavedFact.objects.create(user=user, kind="bill_alias", label="برق خانه", value="THRHOME01", origin_fa="x")
    r3 = process_message(user, "قبض برق خانه رو بررسی کن")
    t3 = Task.objects.get(id=r3["tasks"][0]["id"])
    # bill still needs consent then fail
    assert Task.objects.get(id=r1["tasks"][0]["id"]).execution_state == ExecutionState.DELIVERED
    assert Task.objects.get(id=r2["tasks"][0]["id"]).execution_state == ExecutionState.DELIVERED
    assert t3.execution_state in {ExecutionState.NEEDS_INFORMATION, ExecutionState.FAILED}


@pytest.mark.django_db
def test_ac39_operator_disable(user, operator, client):
    client.force_login(operator)
    r = client.post(
        "/api/ops/capabilities/disable/",
        {"slug": "electricity_bill", "disabled": True},
        content_type="application/json",
    )
    assert r.status_code == 200
    result = process_message(user, "قبض برق خانه رو بررسی کن")
    task = Task.objects.get(id=result["tasks"][0]["id"])
    assert task.execution_state == ExecutionState.BLOCKED
    result2 = process_message(user, "فردا ساعت ۱۰ یادم بنداز دارو")
    assert Task.objects.get(id=result2["tasks"][0]["id"]).execution_state == ExecutionState.DELIVERED


@pytest.mark.django_db
def test_ac40_limit_unknown_recovery(user, auth_client):
    serialize_entitlement(user)
    # exhaust
    from apps.billing.models import Entitlement

    e = Entitlement.objects.get(user=user)
    e.task_runs_consumed = e.plan.task_run_limit
    e.save()
    task = Task.objects.create(
        user=user,
        kind=TaskKind.SERVICE_REQUEST,
        title="x",
        original_goal="x",
        agreed_deliverable="x",
        execution_state=ExecutionState.OUTCOME_UNKNOWN,
        external_outcome=ExternalOutcome.UNKNOWN,
    )
    r = auth_client.get("/api/tasks/?filter=attention")
    ids = [t["id"] for t in r.json()["tasks"]]
    assert task.id in ids
    r = auth_client.post(f"/api/tasks/{task.id}/", {"action": "stop"}, content_type="application/json")
    assert r.status_code == 200


@pytest.mark.django_db
def test_ac41_provider_failure_restores(user):
    from apps.billing.services import ensure_entitlement

    ensure_entitlement(user)
    before = remaining_runs(user.entitlement)
    ok = reserve_run(user, task_id=None, reason="test")
    assert ok
    restore_run(user, task_id=None, reason="provider_failure")
    user.entitlement.refresh_from_db()
    assert remaining_runs(user.entitlement) == before


@pytest.mark.django_db
def test_ac42_sms_exhausted_keeps_inbox(user):
    from apps.billing.services import ensure_entitlement
    from apps.notifications.services import notify_inbox

    e = ensure_entitlement(user)
    e.sms_consumed = e.plan.sms_limit
    e.save()
    user.sms_opt_in = True
    user.save()
    n = notify_inbox(user, title_fa="یادآور", body_fa="x", sms=True)
    assert n.channel == "inbox"
    from apps.notifications.models import Notification

    sms_notes = Notification.objects.filter(user=user, delivery_status="skipped_sms_exhausted")
    assert sms_notes.exists() or n.delivery_status == "delivered"


@pytest.mark.django_db
def test_ac43_delete_account(auth_client, user):
    process_message(user, "فردا ساعت ۱۰ یادم بنداز")
    from apps.reminders.models import Reminder

    r = auth_client.post("/api/auth/delete/", {}, content_type="application/json")
    assert r.status_code == 200
    user.refresh_from_db()
    assert user.is_active is False
    assert Reminder.objects.filter(user=user, cancelled_at__isnull=True).count() == 0


@pytest.mark.django_db
def test_ac44_operator_cannot_open_unrelated(operator, user, client):
    task = Task.objects.create(
        user=user, kind=TaskKind.PERSONAL, title="private", original_goal="g", agreed_deliverable="d"
    )
    client.force_login(operator)
    r = client.post(f"/api/ops/tasks/{task.id}/", {}, content_type="application/json")
    assert r.status_code == 403


@pytest.mark.django_db
def test_ac45_no_cross_account(user, operator):
    other = process_message(operator, "فردا ساعت ۱۰ یادم بنداز دارو")
    other_id = other["tasks"][0]["id"]
    mine = Task.objects.filter(user=user, id=other_id)
    assert not mine.exists()


@pytest.mark.django_db
def test_ac46_repeat_payment_return(auth_client, user):
    r = auth_client.post("/api/billing/checkout/", {}, content_type="application/json")
    authority = r.json()["authority"]
    auth_client.get(f"/api/billing/sandbox/pay/?authority={authority}")
    v1 = auth_client.post("/api/billing/verify/", {"authority": authority}, content_type="application/json")
    v2 = auth_client.post("/api/billing/verify/", {"authority": authority}, content_type="application/json")
    assert v1.json().get("activated") is True
    assert v2.json().get("already_verified") is True
    assert SubscriptionPayment.objects.filter(user=user, status="verified").count() == 1


@pytest.mark.django_db
def test_qual01_task_survives(user, auth_client):
    result = process_message(user, "فردا ساعت ۱۰ یادم بنداز")
    tid = result["tasks"][0]["id"]
    r = auth_client.get(f"/api/tasks/{tid}/")
    assert r.status_code == 200
    assert r.json()["id"] == tid


@pytest.mark.django_db
def test_qual06_provider_down_agenda_ok(user, auth_client):
    Capability.objects.filter(slug="electricity_bill").update(operator_disabled=True)
    process_message(user, "فردا ساعت ۱۰ یادم بنداز دارو")
    r = auth_client.get("/api/reminders/agenda/?view=upcoming")
    assert r.status_code == 200
    assert "تقویم خارجی" in r.json()["disclaimer_fa"]
    r = auth_client.get("/api/auth/me/")
    assert r.status_code == 200
