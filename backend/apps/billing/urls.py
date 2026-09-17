from django.urls import path

from apps.billing import views

urlpatterns = [
    path("plans/", views.plans, name="plans"),
    path("checkout/", views.checkout, name="checkout"),
    path("sandbox/pay/", views.sandbox_pay, name="sandbox-pay"),
    path("verify/", views.verify, name="billing-verify"),
]
