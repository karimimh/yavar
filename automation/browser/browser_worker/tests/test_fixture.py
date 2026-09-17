from browser_worker.submit_form import FIXTURE


def test_sandbox_form_submission_is_evidenced() -> None:
    assert FIXTURE.exists()
    html = FIXTURE.read_text(encoding="utf-8")
    assert "غیرالزام‌آور" in html
    assert "ارسال درخواست نوبت" in html
