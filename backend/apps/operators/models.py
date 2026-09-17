from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="operator_actions"
    )
    action = models.CharField(max_length=64)
    target_type = models.CharField(max_length=64)
    target_id = models.CharField(max_length=64, blank=True)
    summary_fa = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class SupportIncident(models.Model):
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="incidents"
    )
    task = models.ForeignKey("tasks.Task", null=True, blank=True, on_delete=models.SET_NULL)
    message = models.TextField()
    consent_share_task = models.BooleanField(default=False)
    redacted_context = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class SafetyIncident(models.Model):
    """Unauthorized submit / leak / duplicate / false-success → disable execution path."""

    kind = models.CharField(max_length=64)
    capability_slug = models.CharField(max_length=64, blank=True)
    summary_fa = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    path_disabled = models.BooleanField(default=True)
