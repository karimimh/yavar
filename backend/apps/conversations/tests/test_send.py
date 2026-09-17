import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image


def _png() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), color=(12, 24, 36)).save(buf, format="PNG")
    return buf.getvalue()


@pytest.mark.django_db
def test_ac06_duplicate_screenshot_warns(auth_client):
    content = _png()
    upload = SimpleUploadedFile("a.png", content, content_type="image/png")
    r1 = auth_client.post("/api/conversations/send/", {"text": "", "screenshot": upload})
    assert r1.status_code == 200
    upload2 = SimpleUploadedFile("a.png", content, content_type="image/png")
    r2 = auth_client.post("/api/conversations/send/", {"text": "", "screenshot": upload2})
    assert r2.status_code == 200
    assert r2.json().get("duplicate_screenshot") or r2.json().get("duplicate_screenshot_warning_fa")


@pytest.mark.django_db
def test_send_message_creates_task(auth_client):
    r = auth_client.post(
        "/api/conversations/send/",
        {"text": "فردا ساعت ۱۰ یادم بنداز قبض"},
        content_type="application/json",
    )
    assert r.status_code == 200
    assert r.json()["tasks"]
    assert r.json()["tasks"][0]["id"]


@pytest.mark.django_db
def test_qual02_ack_fast(auth_client):
    import time

    start = time.perf_counter()
    r = auth_client.post(
        "/api/conversations/send/",
        {"text": "فردا ساعت ۱۰ یادم بنداز"},
        content_type="application/json",
    )
    elapsed = time.perf_counter() - start
    assert r.status_code == 200
    assert elapsed < 3
