from __future__ import annotations

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone as dj_timezone


class UserManager(BaseUserManager):
    def _create_user(self, phone: str, password: str | None = None, **extra):
        if not phone:
            raise ValueError("phone is required")
        extra.setdefault("phone_original", extra.get("phone_original", phone))
        user = self.model(phone=phone, **extra)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user(self, phone: str, password: str | None = None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(phone, password, **extra)

    def create_superuser(self, phone: str, password: str | None = None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("is_operator", True)
        return self._create_user(phone, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    phone = models.CharField(max_length=16, unique=True)
    phone_original = models.CharField(max_length=32, blank=True)
    preferred_name = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    usual_departure_city = models.CharField(max_length=100, blank=True)
    timezone = models.CharField(max_length=64, default="Asia/Tehran")
    week_starts_on = models.CharField(max_length=16, default="saturday")
    display_currency = models.CharField(max_length=16, default="toman")
    default_reminder_time = models.TimeField(null=True, blank=True)
    sms_opt_in = models.BooleanField(default=False)
    terms_accepted_at = models.DateTimeField(null=True, blank=True)
    privacy_accepted_at = models.DateTimeField(null=True, blank=True)
    onboarding_completed_at = models.DateTimeField(null=True, blank=True)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    improvement_consent = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_operator = models.BooleanField(default=False)
    is_suspended = models.BooleanField(default=False)
    deletion_requested_at = models.DateTimeField(null=True, blank=True)
    deletion_due_at = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(default=dj_timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self) -> str:
        return self.phone


class OneTimeCode(models.Model):
    phone = models.CharField(max_length=16, db_index=True)
    code_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)
    attempt_count = models.PositiveSmallIntegerField(default=0)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]


class OtpThrottle(models.Model):
    """Persisted rate-limit counters for OTP request/resend (works without Redis in tests)."""

    key = models.CharField(max_length=80, unique=True)
    window_started_at = models.DateTimeField()
    count = models.PositiveIntegerField(default=0)


class TimezoneChangeProposal(models.Model):
    """AC-04: timezone change asks keep-instant vs keep-local-clock before applying to reminders."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="timezone_proposals")
    old_timezone = models.CharField(max_length=64)
    new_timezone = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    choice = models.CharField(max_length=32, blank=True)  # keep_instant | keep_local_clock
