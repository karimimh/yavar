from django.conf import settings
from django.db import models


class Conversation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations")
    title = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-updated_at"]


class Message(models.Model):
    ROLE_CHOICES = (("user", "user"), ("assistant", "assistant"), ("system", "system"))
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=16, choices=ROLE_CHOICES)
    text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    contains_secret_warning = models.BooleanField(default=False)
    secret_redacted = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]


class Attachment(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="attachments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="screenshots/%Y/%m/")
    content_type = models.CharField(max_length=64)
    size_bytes = models.PositiveIntegerField()
    sha256 = models.CharField(max_length=64, db_index=True)
    retain_original = models.BooleanField(default=False)
    original_deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    duplicate_of = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)
