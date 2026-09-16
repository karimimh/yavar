"""
Infrastructure verification: confirm Playwright is installed and Chromium can
launch headlessly. No website automation is performed.
"""

from playwright.sync_api import sync_playwright


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        version = browser.version
        browser.close()
    print(f"Playwright OK - Chromium {version} launched and closed successfully.")


if __name__ == "__main__":
    main()
