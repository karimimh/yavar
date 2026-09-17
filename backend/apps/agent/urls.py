from django.urls import path

from apps.agent import views

urlpatterns = [
    path("extraction/<int:pk>/confirm/", views.confirm_extraction, name="extraction-confirm"),
]
