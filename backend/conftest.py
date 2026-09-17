from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.accounts.services import get_sms_provider
from apps.accounts.sms import MemorySmsProvider
from apps.agent.llm import set_llm_client
from apps.billing.services import seed_plans
from apps.bills import adapters as bill_adapters
from apps.coverage.seed import seed_capabilities
from apps.requests import adapters as request_adapters
from apps.travel import adapters as travel_adapters


@pytest.fixture(autouse=True)
def _fast_hasher(settings):
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
    settings.SMS_PROVIDER = "memory"
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True


@pytest.fixture(autouse=True)
def _seed(db):
    seed_capabilities()
    seed_plans()
    request_adapters.reset()
    travel_adapters.set_alpha_down(False)
    travel_adapters.set_price_change(False)
    bill_adapters.set_live_fail(False)
    bill_adapters.set_unexpected_redirect(False)
    set_llm_client(None)
    yield
    set_llm_client(None)
    request_adapters.reset()


@pytest.fixture
def user(db):
    User = get_user_model()
    return User.objects.create_user(
        phone="+989121111111",
        phone_original="09121111111",
        timezone="Asia/Tehran",
        preferred_name="آزمایش",
    )


@pytest.fixture
def operator(db):
    User = get_user_model()
    return User.objects.create_user(
        phone="+989120000001",
        phone_original="09120000001",
        is_staff=True,
        is_operator=True,
    )


@pytest.fixture
def auth_client(client: Client, user):
    client.force_login(user)
    return client


@pytest.fixture
def sms():
    provider = get_sms_provider()
    if not isinstance(provider, MemorySmsProvider):
        provider = MemorySmsProvider()
    provider.clear()
    return provider
