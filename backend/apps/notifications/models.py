from django.conf import settings
from django.db import models


class Notification(models.Model):
    CHANNEL_CHOICES = (("inbox", "inbox"), ("sms", "sms"))
    DELIVERY_CHOICES = (
        ("requested", "requested"),
        ("accepted", "accepted"),
        ("delivered", "delivered"),
        ("unknown", "unknown"),
        ("skipped_quiet_hours", "skipped_quiet_hours"),
        ("skipped_sms_exhausted", "skipped_sms_exhausted"),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    task = models.ForeignKey("tasks.Task", null=True, blank=True, on_delete=models.SET_NULL)
    reminder = models.ForeignKey("reminders.Reminder", null=True, blank=True, on_delete=models.SET_NULL)
    channel = models.CharField(max_length=16, choices=CHANNEL_CHOICES, default="inbox")
    title_fa = models.CharField(max_length=200)
    body_fa = models.TextField()
    generic_sms_body = models.CharField(max_length=160, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    delivery_status = models.CharField(max_length=32, choices=DELIVERY_CHOICES, default="requested")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
