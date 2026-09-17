from django.urls import path

from apps.accounts import privacy, views

urlpatterns = [
    path("csrf/", views.csrf, name="csrf"),
    path("otp/request/", views.otp_request, name="otp-request"),
    path("otp/verify/", views.otp_verify, name="otp-verify"),
    path("logout/", views.logout_view, name="logout"),
    path("me/", views.me, name="me"),
    path("onboarding/", views.complete_onboarding, name="onboarding"),
    path("preferences/", views.update_preferences, name="preferences"),
    path("timezone/resolve/", views.resolve_timezone_change, name="timezone-resolve"),
    path("export/", privacy.export_data, name="export"),
    path("delete/", privacy.delete_account, name="delete-account"),
    path("attachments/<int:pk>/delete/", privacy.delete_attachment, name="delete-attachment"),
]
