from apps.core.enums import CapabilityStatus
from apps.core.labels import SANDBOX_LABEL_FA, capability_status_label
from apps.coverage.models import Capability, OperatorSettings


def get_capability(slug: str) -> Capability | None:
    return Capability.objects.filter(slug=slug).first()


def consult(slug: str) -> dict:
    cap = get_capability(slug)
    if cap is None:
        return {
            "slug": slug,
            "status": CapabilityStatus.NOT_SUPPORTED,
            "executable": False,
            "sandbox": True,
            "label_fa": capability_status_label(CapabilityStatus.NOT_SUPPORTED, True),
            "reason_fa": "این اقدام در فهرست قابلیت‌ها نیست.",
        }
    status = cap.effective_status()
    return {
        "slug": cap.slug,
        "name_fa": cap.name_fa,
        "status": status,
        "executable": cap.is_executable(),
        "sandbox": cap.sandbox,
        "label_fa": capability_status_label(status, cap.sandbox),
        "geography_note_fa": cap.geography_note_fa,
        "required_user_steps_fa": cap.required_user_steps_fa,
        "identifier_type": cap.identifier_type,
        "supports_handoff": cap.supports_handoff,
        "supports_submit": cap.supports_submit,
        "operator_disabled": cap.operator_disabled,
        "pause_all_submissions": OperatorSettings.get().pause_all_external_submissions,
        "sandbox_label_fa": SANDBOX_LABEL_FA if cap.sandbox else "",
    }


def require_executable(slug: str) -> tuple[bool, dict]:
    info = consult(slug)
    return info["executable"], info


def serialize_capability(cap: Capability) -> dict:
    status = cap.effective_status()
    return {
        "slug": cap.slug,
        "name_fa": cap.name_fa,
        "description_fa": cap.description_fa,
        "category": cap.category,
        "status": status,
        "status_label_fa": capability_status_label(status, cap.sandbox),
        "sandbox": cap.sandbox,
        "sandbox_label_fa": SANDBOX_LABEL_FA if cap.sandbox else None,
        "geography_note_fa": cap.geography_note_fa,
        "required_user_steps_fa": cap.required_user_steps_fa,
        "identifier_type": cap.identifier_type,
        "supports_handoff": cap.supports_handoff,
        "supports_submit": cap.supports_submit,
        "validation_metadata": cap.validation_metadata or {},
        "live_brand_claimed": bool((cap.validation_metadata or {}).get("live_validated")),
    }
