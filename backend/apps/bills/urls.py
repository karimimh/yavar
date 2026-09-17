from django.urls import path

from apps.bills import views

urlpatterns = [
    path("tasks/<int:pk>/pay/", views.payment_handoff, name="bill-pay"),
    path("tasks/<int:pk>/pay/return/", views.payment_return, name="bill-pay-return"),
]
