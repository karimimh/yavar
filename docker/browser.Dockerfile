# Browser worker environment: Python + Playwright + Chromium.
# The base image ships the browsers and all headless Chromium system
# dependencies; the image tag must match the playwright version pinned in
# automation/browser/pyproject.toml so the browsers are compatible.
FROM mcr.microsoft.com/playwright/python:v1.63.0-noble

RUN pip install --no-cache-dir --break-system-packages playwright==1.63.0

WORKDIR /app

COPY . .

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Verify Playwright/Chromium on startup, then idle until real worker
# processes are implemented.
CMD ["bash", "-c", "python -m browser_worker.verify && sleep infinity"]
