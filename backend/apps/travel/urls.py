from django.urls import path

from apps.travel import views

urlpatterns = [
    path("tasks/<int:pk>/select/", views.select_offer, name="travel-select"),
]
