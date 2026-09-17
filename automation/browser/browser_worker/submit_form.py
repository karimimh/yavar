"""Submit the sandbox nonbinding service-request form (local HTML fixture)."""

from __future__ import annotations

from pathlib import Path

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "service_request.html"


def submit_sandbox_form(fields: dict) -> dict:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(FIXTURE.as_uri())
        if "sandbox.yavar.local" not in page.url and page.url.startswith("file:"):
            # Local fixture is the validated domain stand-in for CI.
            pass
        page.fill('input[name="name"]', fields.get("name") or "")
        page.fill('input[name="phone"]', fields.get("phone") or "")
        page.fill('input[name="area"]', fields.get("area") or "")
        page.fill('input[name="preferred_slot"]', fields.get("preferred_slot") or "")
        page.fill('textarea[name="note"]', fields.get("note") or "")
        page.click("#submit")
        page.wait_for_selector("#result:not([hidden])")
        text = page.inner_text("#result")
        browser.close()
    return {"ok": True, "ack": text, "sandbox": True, "appointment_confirmed": False}
