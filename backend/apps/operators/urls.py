from django.urls import path

from apps.operators import support_views, views

urlpatterns = [
    path("dashboard/", views.dashboard, name="ops-dashboard"),
    path("capabilities/disable/", views.disable_capability, name="ops-disable"),
    path("pause-submissions/", views.pause_submissions, name="ops-pause"),
    path("suspend/", views.suspend_account, name="ops-suspend"),
    path("restore-credits/", views.restore_credits, name="ops-restore"),
    path("incidents/<int:pk>/", views.incident_trail, name="ops-incident"),
    path("tasks/<int:pk>/", views.open_task, name="ops-open-task"),
    path("report/", support_views.report_issue, name="report-issue"),
]
