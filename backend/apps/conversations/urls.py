from django.urls import path

from apps.conversations import views

urlpatterns = [
    path("", views.conversations, name="conversations"),
    path("send/", views.send_message, name="conversation-send"),
    path("<int:pk>/", views.conversation_detail, name="conversation-detail"),
    path("messages/<int:pk>/delete/", views.delete_message, name="message-delete"),
]
