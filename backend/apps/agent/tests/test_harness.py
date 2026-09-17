"""Sandbox scenario harness. Live-provider cases are skipped until validation metadata exists."""

from __future__ import annotations

import pytest

from apps.agent.runtime import process_message
from apps.core.enums import ExecutionState
from apps.tasks.models import Task

SANDBOX_SCENARIOS = [
    ("s01_reminder_tomorrow", "فردا ساعت ۱۰ یادم بنداز دارو"),
    ("s02_reminder_today_time", "امروز ساعت ۱۸ یادم بنداز تماس"),
    ("s03_daily", "هر روز ساعت ۸ یادم بنداز دارو"),
    ("s04_weekly", "هر هفته ساعت ۹ یادم بنداز جلسه"),
    ("s05_flight_thr_syz", "بلیط تهران به شیراز پیدا کن"),
    ("s06_flight_budget", "بلیط تهران به مشهد زیر ۳ میلیون"),
    ("s07_flight_morning", "پرواز تهران به اصفهان فقط صبح"),
    ("s08_shop_compare", "هدفون مدل X مقایسه کن"),
    ("s09_internet_mobile", "بسته اینترنت همراه مقایسه کن"),
    ("s10_internet_fixed", "اینترنت ثابت مقایسه کن"),
    ("s11_local_hours", "تعویض روغن در تهران مقایسه کن"),
    ("s12_service_request", "شنبه ساعت ۱۰ برای تعویض روغن یه وقت بگیر"),
    ("s13_personal", "لیست خرید این هفته"),
    ("s14_unsupported_hotel", "هتل شیراز رزرو کن"),
    ("s15_two_intents", "فردا ساعت ۱۰ یادم بنداز و هدفون مدل X مقایسه کن"),
    ("s16_bill_inquiry", "قبض برق خانه رو بررسی کن"),
    ("s17_flight_tabriz", "بلیط تهران به تبریز پیدا کن"),
    ("s18_quiet_hours", "فردا ساعت ۲۳ یادم بنداز دارو"),
    ("s19_takeover_request", "برای تعویض روغن یک وقت بگیر"),
]


@pytest.mark.django_db
@pytest.mark.parametrize("name,text", SANDBOX_SCENARIOS)
def test_sandbox_nominal_scenarios(user, name, text):
    result = process_message(user, text)
    assert result["conversation_id"]
    assert "tasks" in result


LIVE_PROVIDER_PENDING = [
    "live_flight_alpha_real_brand",
    "live_flight_beta_real_brand",
    "live_electricity_real_provider",
    "live_service_form_real_shop",
    "live_sms_gateway_deliverability",
]


@pytest.mark.skip(reason="Live Iranian provider not validated (spec 17.1 / 23.3)")
@pytest.mark.parametrize("name", LIVE_PROVIDER_PENDING)
def test_live_provider_pending(name):
    raise AssertionError("should be skipped")


@pytest.mark.django_db
def test_independent_tasks_in_one_thread(user):
    result = process_message(user, "بلیط تهران به شیراز پیدا کن و قبض برق خانه رو بررسی کن")
    assert len(result["tasks"]) >= 2
    ids = [t["id"] for t in result["tasks"]]
    t1, t2 = Task.objects.filter(id__in=ids)
    assert t1.id != t2.id
    assert t1.execution_state != ExecutionState.CANCELLED or t2.execution_state != ExecutionState.CANCELLED
