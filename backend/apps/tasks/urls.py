from django.urls import path

from apps.tasks import views

urlpatterns = [
    path("", views.task_list, name="task-list"),
    path("<int:pk>/", views.task_detail, name="task-detail"),
    path("<int:pk>/clarify/", views.clarify, name="task-clarify"),
]
