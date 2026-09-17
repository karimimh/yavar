from django.urls import path

from apps.reminders import views

urlpatterns = [
    path("", views.reminder_list, name="reminder-list"),
    path("agenda/", views.agenda_view, name="agenda"),
    path("<int:pk>/", views.reminder_action, name="reminder-action"),
]
