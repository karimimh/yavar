from django.urls import path

from apps.approvals import views

urlpatterns = [
    path("<int:pk>/", views.approval_detail, name="approval-detail"),
    path("<int:pk>/decide/", views.approval_decide, name="approval-decide"),
]
