from django.conf import settings
from django.db import models

from apps.core.enums import EvidenceType, ExecutionState, ExternalOutcome, TaskKind


class Task(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tasks")
    conversation = models.ForeignKey(
        "conversations.Conversation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )
    kind = models.CharField(max_length=32, choices=TaskKind.choices)
    title = models.CharField(max_length=300)
    original_goal = models.TextField()
    agreed_deliverable = models.TextField()
    original_wording = models.TextField(blank=True)
    constraints = models.JSONField(default=dict, blank=True)
    plan_checklist = models.JSONField(default=list, blank=True)
    execution_state = models.CharField(
        max_length=32, choices=ExecutionState.choices, default=ExecutionState.QUEUED
    )
    external_outcome = models.CharField(
        max_length=32, choices=ExternalOutcome.choices, default=ExternalOutcome.NOT_SUBMITTED
    )
    remaining_work = models.TextField(blank=True)
    stop_requested_at = models.DateTimeField(null=True, blank=True)
    run_started_at = models.DateTimeField(null=True, blank=True)
    work_deadline_at = models.DateTimeField(null=True, blank=True)
    input_wait_expires_at = models.DateTimeField(null=True, blank=True)
    current_activity_fa = models.CharField(max_length=300, blank=True)
    last_error_fa = models.TextField(blank=True)
    read_retry_count = models.PositiveSmallIntegerField(default=0)
    allowance_reserved = models.BooleanField(default=False)
    allowance_consumed = models.BooleanField(default=False)
    capability_slug = models.CharField(max_length=64, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]


class Step(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="steps")
    name = models.CharField(max_length=120)
    name_fa = models.CharField(max_length=200)
    status = models.CharField(max_length=32, default="pending")
    permission_level = models.CharField(max_length=32, default="public_read")
    provider_slug = models.CharField(max_length=64, blank=True)
    detail = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)


class TaskEvent(models.Model):
    """Append-only history. Corrections add events; they do not rewrite consequential rows."""

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="events")
    kind = models.CharField(max_length=64)
    summary_fa = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class OutcomeEvidence(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="evidence")
    evidence_type = models.CharField(max_length=32, choices=EvidenceType.choices)
    summary_fa = models.TextField()
    proves = models.CharField(max_length=120)
    provider = models.CharField(max_length=120, blank=True)
    reference = models.CharField(max_length=120, blank=True)
    origin = models.CharField(max_length=32, default="system")  # system | provider | user
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Offer(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="offers")
    source_slug = models.CharField(max_length=64)
    provider_name_fa = models.CharField(max_length=120)
    title = models.CharField(max_length=300)
    attributes = models.JSONField(default=dict, blank=True)
    amount = models.DecimalField(max_digits=14, decimal_places=0, null=True, blank=True)
    unit = models.CharField(max_length=16, blank=True)
    fees = models.JSONField(default=list, blank=True)
    source_url = models.URLField(blank=True)
    retrieved_at = models.DateTimeField()
    is_match = models.BooleanField(default=True)
    violated_constraint = models.CharField(max_length=200, blank=True)
    ranking_note_fa = models.TextField(blank=True)
    unverified_fields = models.JSONField(default=list, blank=True)
    sandbox = models.BooleanField(default=True)
    handoff_url = models.URLField(blank=True)
    preserves_offer = models.BooleanField(default=True)


class Draft(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="drafts")
    kind = models.CharField(max_length=32)
    fields = models.JSONField(default=dict)
    recipient_fa = models.CharField(max_length=200, blank=True)
    destination = models.CharField(max_length=300, blank=True)
    nonbinding = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
