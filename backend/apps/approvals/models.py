from django.conf import settings
from django.db import models


class Approval(models.Model):
    STATUS_CHOICES = (
        ("pending", "pending"),
        ("approved", "approved"),
        ("used", "used"),
        ("expired", "expired"),
        ("invalidated", "invalidated"),
        ("cancelled", "cancelled"),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="approvals")
    task = models.ForeignKey("tasks.Task", on_delete=models.CASCADE, related_name="approvals")
    action_name = models.CharField(max_length=120)
    action_label_fa = models.CharField(max_length=200)
    recipient_fa = models.CharField(max_length=200)
    destination = models.CharField(max_length=300)
    fields_snapshot = models.JSONField(default=dict)
    costs_fa = models.TextField()
    will_happen_fa = models.TextField()
    will_not_happen_fa = models.TextField()
    confirmation_how_fa = models.TextField()
    fingerprint = models.CharField(max_length=64)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    decided_at = models.DateTimeField(null=True, blank=True)
    used_at = models.DateTimeField(null=True, blank=True)
    attempt_started = models.BooleanField(default=False)
    submission_id = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ["-created_at"]
