from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", include("apps.core.urls")),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/coverage/", include("apps.coverage.urls")),
    path("api/conversations/", include("apps.conversations.urls")),
    path("api/tasks/", include("apps.tasks.urls")),
    path("api/reminders/", include("apps.reminders.urls")),
    path("api/approvals/", include("apps.approvals.urls")),
    path("api/memory/", include("apps.memory.urls")),
    path("api/notifications/", include("apps.notifications.urls")),
    path("api/billing/", include("apps.billing.urls")),
    path("api/travel/", include("apps.travel.urls")),
    path("api/bills/", include("apps.bills.urls")),
    path("api/agent/", include("apps.agent.urls")),
    path("api/ops/", include("apps.operators.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
