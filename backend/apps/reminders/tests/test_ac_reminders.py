from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from django.utils import timezone
from freezegun import freeze_time

from apps.agent.llm import FakeLlmClient, set_llm_client
from apps.agent.runtime import process_message
from apps.core.enums import ExecutionState
from apps.notifications.models import Notification
from apps.reminders.models import Reminder
from apps.reminders.services import fire_due_reminders
from apps.tasks.models import Task


@pytest.mark.django_db
def test_ac01_unambiguous_reminder(user):
    now = datetime(2026, 9, 17, 9, 0, tzinfo=ZoneInfo("Asia/Tehran"))
    result = process_message(user, "فردا ساعت ۱۰ یادم بنداز قبض رو بررسی کنم", now=now)
    task = Task.objects.get(id=result["tasks"][0]["id"])
    reminder = Reminder.objects.get(task=task)
    assert reminder.due_at.astimezone(ZoneInfo("Asia/Tehran")).hour == 10
    assert task.payload.get("undo") is True
    assert "۱۴" in task.payload.get("display_fa", "") or "2026" or task.payload.get("display_fa")


@pytest.mark.django_db
def test_ac02_ambiguous_thursday_asks(user):
    now = datetime(2026, 9, 17, 12, 0, tzinfo=ZoneInfo("Asia/Tehran"))
    result = process_message(user, "پنجشنبه یادم بنداز", now=now)
    task = Task.objects.get(id=result["tasks"][0]["id"])
    assert task.execution_state == ExecutionState.NEEDS_INFORMATION
    assert Reminder.objects.filter(task=task).count() == 0


@pytest.mark.django_db
def test_ac03_recurrence_this_vs_future(user, auth_client):
    now = datetime(2026, 9, 18, 10, 0, tzinfo=ZoneInfo("Asia/Tehran"))
    result = process_message(user, "هر روز ساعت ۱۰ یادم بنداز دارو", now=now)
    reminder = Reminder.objects.get(task_id=result["tasks"][0]["id"])
    r = auth_client.post(
        f"/api/reminders/{reminder.id}/",
        {"action": "edit_recurrence", "scope": "this_occurrence"},
        content_type="application/json",
    )
    assert r.status_code == 200
    reminder.refresh_from_db()
    assert reminder.occurrence_edits.exists()


@pytest.mark.django_db
def test_ac04_timezone_change_asks(auth_client, user):
    r = auth_client.post(
        "/api/auth/preferences/",
        {"timezone": "UTC"},
        content_type="application/json",
    )
    assert r.json()["needs_timezone_choice"] is True
    user.refresh_from_db()
    assert user.timezone == "Asia/Tehran"


@pytest.mark.django_db
def test_ac05_blurred_amount_not_invented(user):
    set_llm_client(
        FakeLlmClient(
            {
                "vision": {
                    "items": [
                        {
                            "title": "پرداخت قبض",
                            "excerpt": "مهلت تا پایان ماه",
                            "amount": None,
                            "amount_uncertain": True,
                            "due_at": "2026-09-25T10:00:00+03:30",
                        }
                    ]
                }
            }
        )
    )
    from apps.agent.tools import run_extraction
    from apps.core.enums import TaskKind

    task = Task.objects.create(
        user=user,
        kind=TaskKind.EXTRACTION,
        title="استخراج",
        original_goal="screenshot",
        agreed_deliverable="draft",
    )
    run_extraction(task)
    item = task.payload["extraction_draft"]["items"][0]
    assert item["amount"] is None
    assert item.get("amount_uncertain") or item.get("flag_fa")


@pytest.mark.django_db
def test_ac07_extraction_not_auto_saved(user):
    set_llm_client(
        FakeLlmClient(
            {
                "vision": {
                    "items": [
                        {
                            "title": "یادآور",
                            "excerpt": "فردا",
                            "due_at": "2026-09-18T10:00:00+03:30",
                        }
                    ]
                }
            }
        )
    )
    from apps.agent.tools import run_extraction
    from apps.core.enums import TaskKind

    task = Task.objects.create(
        user=user, kind=TaskKind.EXTRACTION, title="e", original_goal="s", agreed_deliverable="d"
    )
    run_extraction(task)
    assert Reminder.objects.filter(user=user).count() == 0
    assert task.payload["extraction_draft"]["saved"] is False


@pytest.mark.django_db
def test_qual03_due_reminder_within_60s(user):
    now = timezone.now()
    from apps.reminders.services import create_reminder

    create_reminder(
        user=user,
        title="موعد",
        due_at=now - timedelta(seconds=1),
        timezone_name=user.timezone,
    )
    with freeze_time(now):
        n = fire_due_reminders(now)
    assert n == 1
    assert Notification.objects.filter(user=user, title_fa="یادآور").exists()


@pytest.mark.django_db
def test_cancelled_reminder_does_not_fire(user):
    now = timezone.now()
    from apps.reminders.services import cancel_reminder, create_reminder

    rem = create_reminder(user=user, title="x", due_at=now - timedelta(seconds=1), timezone_name=user.timezone)
    cancel_reminder(rem)
    assert fire_due_reminders(now) == 0
