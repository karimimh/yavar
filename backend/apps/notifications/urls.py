from django.urls import path

from apps.notifications import views

urlpatterns = [
    path("", views.inbox, name="inbox"),
    path("<int:pk>/read/", views.mark_read, name="notification-read"),
]
