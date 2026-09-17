from decimal import Decimal

from django.db import models

from apps.accounts.models import User
from apps.core.enums import PlanCode


class Plan(models.Model):
    code = models.CharField(max_length=16, unique=True, choices=PlanCode.choices)
    name_fa = models.CharField(max_length=64)
    price_amount = models.DecimalField(max_digits=12, decimal_places=0, default=Decimal("0"))
    price_unit = models.CharField(max_length=16, default="toman")
    period_days = models.PositiveSmallIntegerField(default=30)
    task_run_limit = models.PositiveIntegerField(default=10)
    sms_limit = models.PositiveIntegerField(default=10)


class Entitlement(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="entitlement")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    task_runs_reserved = models.PositiveIntegerField(default=0)
    task_runs_consumed = models.PositiveIntegerField(default=0)
    task_runs_restored = models.PositiveIntegerField(default=0)
    sms_consumed = models.PositiveIntegerField(default=0)
    pro_activated_at = models.DateTimeField(null=True, blank=True)


class AllowanceLedger(models.Model):
    """Reserve / consume / restore events for audit and AC-41."""

    ACTION_CHOICES = (
        ("reserve", "reserve"),
        ("consume", "consume"),
        ("restore", "restore"),
        ("sms", "sms"),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="allowance_events")
    task_id = models.IntegerField(null=True, blank=True)
    action = models.CharField(max_length=16, choices=ACTION_CHOICES)
    reason = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)


class SubscriptionPayment(models.Model):
    STATUS_CHOICES = (
        ("initiated", "initiated"),
        ("redirected", "redirected"),
        ("verified", "verified"),
        ("failed", "failed"),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments")
    authority = models.CharField(max_length=64, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=0, default=Decimal("299000"))
    unit = models.CharField(max_length=16, default="toman")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="initiated")
    return_seen_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    inquiry_status = models.CharField(max_length=32, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
