from django.db import models

from apps.core.enums import CapabilityStatus


class OperatorSettings(models.Model):
    """Singleton-style row for global operator kill switches."""

    pause_all_external_submissions = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get(cls) -> "OperatorSettings":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Capability(models.Model):
    slug = models.SlugField(unique=True)
    name_fa = models.CharField(max_length=200)
    description_fa = models.TextField()
    category = models.CharField(max_length=50)
    status = models.CharField(
        max_length=32,
        choices=CapabilityStatus.choices,
        default=CapabilityStatus.LIMITED,
    )
    sandbox = models.BooleanField(default=True)
    operator_disabled = models.BooleanField(default=False)
    geography_note_fa = models.TextField(blank=True)
    required_user_steps_fa = models.TextField(blank=True)
    identifier_type = models.CharField(max_length=64, blank=True)
    validation_metadata = models.JSONField(default=dict, blank=True)
    last_validated_at = models.DateTimeField(null=True, blank=True)
    supports_handoff = models.BooleanField(default=False)
    supports_submit = models.BooleanField(default=False)

    def effective_status(self) -> str:
        settings = OperatorSettings.get()
        if self.operator_disabled:
            return CapabilityStatus.TEMPORARILY_UNAVAILABLE
        if settings.pause_all_external_submissions and self.supports_submit:
            return CapabilityStatus.TEMPORARILY_UNAVAILABLE
        return self.status

    def is_executable(self) -> bool:
        status = self.effective_status()
        return status in {CapabilityStatus.AVAILABLE, CapabilityStatus.LIMITED} and not self.operator_disabled
