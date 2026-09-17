from datetime import timedelta

from django.utils import timezone

from apps.core.enums import ACTIVE_EXECUTION_STATES, ExecutionState
from apps.core.labels import execution_label, outcome_label
from apps.tasks.models import OutcomeEvidence, Task, TaskEvent

WORK_LIMIT = timedelta(minutes=10)
INPUT_WAIT = timedelta(hours=24)


def append_event(task: Task, kind: str, summary_fa: str, data: dict | None = None) -> TaskEvent:
    return TaskEvent.objects.create(task=task, kind=kind, summary_fa=summary_fa, data=data or {})


def transition(task: Task, new_state: str, *, activity_fa: str = "", error_fa: str = "") -> Task:
    previous = task.execution_state
    task.execution_state = new_state
    if activity_fa:
        task.current_activity_fa = activity_fa
    if error_fa:
        task.last_error_fa = error_fa
    task.save()
    append_event(
        task,
        "state_change",
        f"وضعیت از {execution_label(previous)} به {execution_label(new_state)}",
        {"from": previous, "to": new_state},
    )
    return task


def set_outcome(task: Task, outcome: str, *, remaining: str = "") -> Task:
    previous = task.external_outcome
    task.external_outcome = outcome
    if remaining:
        task.remaining_work = remaining
    task.save(update_fields=["external_outcome", "remaining_work", "updated_at"])
    append_event(
        task,
        "outcome_change",
        f"نتیجهٔ بیرونی: {outcome_label(outcome)}",
        {"from": previous, "to": outcome},
    )
    return task


def add_evidence(task: Task, **kwargs) -> OutcomeEvidence:
    evidence = OutcomeEvidence.objects.create(task=task, **kwargs)
    append_event(task, "evidence", evidence.summary_fa, {"type": evidence.evidence_type})
    return evidence


def request_stop(task: Task) -> Task:
    task.stop_requested_at = timezone.now()
    task.save(update_fields=["stop_requested_at", "updated_at"])
    if task.execution_state == ExecutionState.CHECKING_RESULT:
        append_event(task, "stop", "توقف هنگام ارسال؛ در حال بررسی اینکه درخواست رسیده یا نه.")
        return transition(task, ExecutionState.CHECKING_RESULT, activity_fa="در حال توقف؛ بررسی دریافت درخواست")
    if task.execution_state in ACTIVE_EXECUTION_STATES:
        return transition(task, ExecutionState.CANCELLED, activity_fa="کار آینده متوقف شد")
    return task


def start_run(task: Task) -> None:
    now = timezone.now()
    task.run_started_at = now
    task.work_deadline_at = now + WORK_LIMIT
    task.save(update_fields=["run_started_at", "work_deadline_at", "updated_at"])


def work_expired(task: Task) -> bool:
    return bool(task.work_deadline_at and timezone.now() > task.work_deadline_at)


def serialize_task(task: Task) -> dict:
    from apps.core.labels import execution_label, outcome_label

    return {
        "id": task.id,
        "kind": task.kind,
        "title": task.title,
        "original_goal": task.original_goal,
        "agreed_deliverable": task.agreed_deliverable,
        "original_wording": task.original_wording,
        "constraints": task.constraints,
        "plan_checklist": task.plan_checklist,
        "execution_state": task.execution_state,
        "execution_state_fa": execution_label(task.execution_state),
        "external_outcome": task.external_outcome,
        "external_outcome_fa": outcome_label(task.external_outcome),
        "remaining_work": task.remaining_work,
        "current_activity_fa": task.current_activity_fa,
        "stop_requested": task.stop_requested_at is not None,
        "can_stop": task.execution_state in ACTIVE_EXECUTION_STATES,
        "payload": task.payload,
        "conversation_id": task.conversation_id,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
        "events": [
            {
                "kind": e.kind,
                "summary_fa": e.summary_fa,
                "created_at": e.created_at.isoformat(),
                "data": e.data,
            }
            for e in task.events.all()
        ],
        "evidence": [
            {
                "type": ev.evidence_type,
                "summary_fa": ev.summary_fa,
                "proves": ev.proves,
                "provider": ev.provider,
                "reference": ev.reference,
                "origin": ev.origin,
                "created_at": ev.created_at.isoformat(),
            }
            for ev in task.evidence.all()
        ],
        "steps": [
            {"name": s.name, "name_fa": s.name_fa, "status": s.status}
            for s in task.steps.all()
        ],
        "latest_approval_id": task.approvals.order_by("-id").values_list("id", flat=True).first(),
    }
