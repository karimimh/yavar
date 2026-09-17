import json

import pytest
from django.test import Client

from apps.accounts.models import User
from apps.accounts.services import request_otp, verify_otp
from apps.coverage.models import Capability


@pytest.mark.django_db
def test_health_endpoint_returns_ok(client: Client) -> None:
    response = client.get("/api/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


@pytest.mark.django_db
def test_otp_login_does_not_reveal_existing_account(sms) -> None:
    first = request_otp("09121111111")
    second = request_otp("09129999999")
    assert first["message"] == second["message"]
    user, err = verify_otp("09121111111", sms.last_code_for("+989121111111"))
    assert err is None
    assert user is not None
    assert User.objects.filter(phone="+989121111111").exists()


@pytest.mark.django_db
def test_otp_api_sets_session(client: Client, sms) -> None:
    r = client.post(
        "/api/auth/otp/request/",
        json.dumps({"phone": "09121111111"}),
        content_type="application/json",
    )
    assert r.status_code == 200
    code = sms.last_code_for("+989121111111")
    assert code
    r = client.post(
        "/api/auth/otp/verify/",
        json.dumps({"phone": "09121111111", "code": code}),
        content_type="application/json",
    )
    assert r.status_code == 200
    me = client.get("/api/auth/me/")
    assert me.status_code == 200
    assert me.json()["phone"] == "+989121111111"


@pytest.mark.django_db
def test_onboarding_timezone(auth_client, user) -> None:
    r = auth_client.post(
        "/api/auth/onboarding/",
        json.dumps(
            {
                "terms_accepted": True,
                "privacy_accepted": True,
                "timezone": "Asia/Tehran",
                "sms_opt_in": False,
            }
        ),
        content_type="application/json",
    )
    assert r.status_code == 200
    user.refresh_from_db()
    assert user.onboarding_completed_at is not None


@pytest.mark.django_db
def test_capability_list_sandbox(client: Client) -> None:
    r = client.get("/api/coverage/")
    assert r.status_code == 200
    data = r.json()
    assert data["provider_mode"] == "sandbox"
    slugs = {c["slug"] for c in data["capabilities"]}
    assert slugs >= {
        "public_research",
        "flight_search_alpha",
        "flight_search_beta",
        "electricity_bill",
        "local_service_request",
    }
    assert all(c["sandbox"] for c in data["capabilities"])
    assert Capability.objects.count() >= 5
