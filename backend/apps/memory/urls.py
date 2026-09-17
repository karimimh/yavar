from django.urls import path

from apps.memory import views

urlpatterns = [
    path("", views.facts, name="facts"),
    path("<int:pk>/", views.fact_detail, name="fact-detail"),
]
