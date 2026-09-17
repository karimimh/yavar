"""Stable snake_case enumerations matching spec sections 12.2, 12.3, and 17.2."""

from django.db import models


class ExecutionState(models.TextChoices):
    QUEUED = "queued", "queued"
    NEEDS_INFORMATION = "needs_information", "needs_information"
    IN_PROGRESS = "in_progress", "in_progress"
    NEEDS_APPROVAL = "needs_approval", "needs_approval"
    NEEDS_USER_TAKEOVER = "needs_user_takeover", "needs_user_takeover"
    CHECKING_RESULT = "checking_result", "checking_result"
    DELIVERED = "delivered", "delivered"
    PARTIALLY_DELIVERED = "partially_delivered", "partially_delivered"
    BLOCKED = "blocked", "blocked"
    FAILED = "failed", "failed"
    CANCELLED = "cancelled", "cancelled"
    EXPIRED = "expired", "expired"
    OUTCOME_UNKNOWN = "outcome_unknown", "outcome_unknown"


class ExternalOutcome(models.TextChoices):
    NOT_SUBMITTED = "not_submitted", "not_submitted"
    PREPARED_ONLY = "prepared_only", "prepared_only"
    REQUEST_RECEIVED = "request_received", "request_received"
    CONFIRMATION_PENDING = "confirmation_pending", "confirmation_pending"
    PROVIDER_CONFIRMED = "provider_confirmed", "provider_confirmed"
    PROVIDER_DECLINED = "provider_declined", "provider_declined"
    USER_REPORTED_COMPLETE = "user_reported_complete", "user_reported_complete"
    UNKNOWN = "unknown", "unknown"


class CapabilityStatus(models.TextChoices):
    AVAILABLE = "available", "available"
    LIMITED = "limited", "limited"
    TEMPORARILY_UNAVAILABLE = "temporarily_unavailable", "temporarily_unavailable"
    NOT_SUPPORTED = "not_supported", "not_supported"


class Recurrence(models.TextChoices):
    ONE_OFF = "one_off", "one_off"
    DAILY = "daily", "daily"
    WEEKLY = "weekly", "weekly"


class TaskKind(models.TextChoices):
    REMINDER = "reminder", "reminder"
    PERSONAL = "personal", "personal"
    RESEARCH = "research", "research"
    TRAVEL_SEARCH = "travel_search", "travel_search"
    TRAVEL_HANDOFF = "travel_handoff", "travel_handoff"
    BILL_INQUIRY = "bill_inquiry", "bill_inquiry"
    BILL_HANDOFF = "bill_handoff", "bill_handoff"
    SERVICE_REQUEST = "service_request", "service_request"
    EXTRACTION = "extraction", "extraction"
    UNSUPPORTED = "unsupported", "unsupported"


class EvidenceType(models.TextChoices):
    IN_APP_RECORD = "in_app_record", "in_app_record"
    PROVIDER_RECEIPT = "provider_receipt", "provider_receipt"
    PROVIDER_REFERENCE = "provider_reference", "provider_reference"
    USER_REPORT = "user_report", "user_report"
    SCREENSHOT_DRAFT = "screenshot_draft", "screenshot_draft"
    LIVE_PROVIDER = "live_provider", "live_provider"
    HANDOFF_PREPARED = "handoff_prepared", "handoff_prepared"
    SOURCE_PAGE = "source_page", "source_page"


class MoneyUnit(models.TextChoices):
    TOMAN = "toman", "toman"
    RIAL = "rial", "rial"
    UNKNOWN = "unknown", "unknown"


class PlanCode(models.TextChoices):
    FREE = "free", "free"
    PRO = "pro", "pro"


ACTIVE_EXECUTION_STATES = frozenset(
    {
        ExecutionState.QUEUED,
        ExecutionState.NEEDS_INFORMATION,
        ExecutionState.IN_PROGRESS,
        ExecutionState.NEEDS_APPROVAL,
        ExecutionState.NEEDS_USER_TAKEOVER,
        ExecutionState.CHECKING_RESULT,
    }
)

TERMINAL_EXECUTION_STATES = frozenset(
    {
        ExecutionState.DELIVERED,
        ExecutionState.PARTIALLY_DELIVERED,
        ExecutionState.BLOCKED,
        ExecutionState.FAILED,
        ExecutionState.CANCELLED,
        ExecutionState.EXPIRED,
        ExecutionState.OUTCOME_UNKNOWN,
    }
)
