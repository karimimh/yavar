from django.conf import settings
from django.db import models

from apps.core.enums import Recurrence


class Reminder(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reminders")
    task = models.ForeignKey(
        "tasks.Task", on_delete=models.SET_NULL, null=True, blank=True, related_name="reminders"
    )
    title = models.CharField(max_length=300)
    details = models.TextField(blank=True)
    timezone = models.CharField(max_length=64)
    due_at = models.DateTimeField()
    local_date = models.DateField()
    local_time = models.TimeField(null=True, blank=True)
    recurrence = models.CharField(max_length=16, choices=Recurrence.choices, default=Recurrence.ONE_OFF)
    weekday = models.PositiveSmallIntegerField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    last_fired_at = models.DateTimeField(null=True, blank=True)
    allow_during_quiet_hours = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["due_at"]


class ReminderOccurrenceEdit(models.Model):
    """Skip or override a single occurrence of a recurring reminder (AC-03)."""

    reminder = models.ForeignKey(Reminder, on_delete=models.CASCADE, related_name="occurrence_edits")
    occurrence_at = models.DateTimeField()
    action = models.CharField(max_length=16)  # skip | reschedule
    new_due_at = models.DateTimeField(null=True, blank=True)
