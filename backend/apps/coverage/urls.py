from django.urls import path

from apps.coverage import views

urlpatterns = [
    path("", views.capability_list, name="capability-list"),
]
