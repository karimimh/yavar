"""Persian labels for user-visible states and outcomes. Spec 12.2 / 12.3 / 14.3."""

from apps.core.enums import CapabilityStatus, ExecutionState, ExternalOutcome

EXECUTION_STATE_FA = {
    ExecutionState.QUEUED: "در صف",
    ExecutionState.NEEDS_INFORMATION: "نیاز به اطلاعات",
    ExecutionState.IN_PROGRESS: "در حال انجام",
    ExecutionState.NEEDS_APPROVAL: "نیاز به تأیید",
    ExecutionState.NEEDS_USER_TAKEOVER: "نیاز به ادامه توسط شما",
    ExecutionState.CHECKING_RESULT: "در حال بررسی نتیجه",
    ExecutionState.DELIVERED: "تحویل‌شده",
    ExecutionState.PARTIALLY_DELIVERED: "تحویل ناقص",
    ExecutionState.BLOCKED: "متوقف‌شده",
    ExecutionState.FAILED: "ناموفق",
    ExecutionState.CANCELLED: "لغوشده",
    ExecutionState.EXPIRED: "منقضی",
    ExecutionState.OUTCOME_UNKNOWN: "نتیجه نامشخص",
}

EXTERNAL_OUTCOME_FA = {
    ExternalOutcome.NOT_SUBMITTED: "ارسال نشده",
    ExternalOutcome.PREPARED_ONLY: "فقط آماده‌سازی",
    ExternalOutcome.REQUEST_RECEIVED: "درخواست دریافت شد",
    ExternalOutcome.CONFIRMATION_PENDING: "تأیید در انتظار",
    ExternalOutcome.PROVIDER_CONFIRMED: "تأیید ارائه‌دهنده",
    ExternalOutcome.PROVIDER_DECLINED: "رد شده توسط ارائه‌دهنده",
    ExternalOutcome.USER_REPORTED_COMPLETE: "تکمیل به گزارش کاربر",
    ExternalOutcome.UNKNOWN: "نامشخص",
}

CAPABILITY_STATUS_FA = {
    CapabilityStatus.AVAILABLE: "در دسترس",
    CapabilityStatus.LIMITED: "محدود",
    CapabilityStatus.TEMPORARILY_UNAVAILABLE: "موقتاً در دسترس نیست",
    CapabilityStatus.NOT_SUPPORTED: "پشتیبانی نمی‌شود",
}

SANDBOX_LABEL_FA = "آزمایشی"


def execution_label(state: str) -> str:
    return EXECUTION_STATE_FA.get(state, state)


def outcome_label(outcome: str) -> str:
    return EXTERNAL_OUTCOME_FA.get(outcome, outcome)


def capability_status_label(status: str, sandbox: bool = False) -> str:
    base = CAPABILITY_STATUS_FA.get(status, status)
    if sandbox:
        return f"{base} — {SANDBOX_LABEL_FA}"
    return base
