from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.billing.models import AllowanceLedger, Entitlement, Plan
from apps.core.enums import PlanCode

PRO_PRICE = 299_000
PRO_UNIT = "toman"


def seed_plans() -> None:
    Plan.objects.update_or_create(
        code=PlanCode.FREE,
        defaults={
            "name_fa": "رایگان",
            "price_amount": 0,
            "price_unit": PRO_UNIT,
            "period_days": 30,
            "task_run_limit": 10,
            "sms_limit": 10,
        },
    )
    Plan.objects.update_or_create(
        code=PlanCode.PRO,
        defaults={
            "name_fa": "حرفه‌ای",
            "price_amount": PRO_PRICE,
            "price_unit": PRO_UNIT,
            "period_days": 30,
            "task_run_limit": 100,
            "sms_limit": 50,
        },
    )


def ensure_entitlement(user: User) -> Entitlement:
    seed_plans()
    now = timezone.now()
    try:
        ent = user.entitlement
    except Entitlement.DoesNotExist:
        plan = Plan.objects.get(code=PlanCode.FREE)
        return Entitlement.objects.create(
            user=user,
            plan=plan,
            period_start=now,
            period_end=now + timedelta(days=plan.period_days),
        )
    if now > ent.period_end:
        ent.period_start = now
        ent.period_end = now + timedelta(days=ent.plan.period_days)
        ent.task_runs_reserved = 0
        ent.task_runs_consumed = 0
        ent.task_runs_restored = 0
        ent.sms_consumed = 0
        # Pro does not auto-renew.
        if ent.plan.code == PlanCode.PRO:
            ent.plan = Plan.objects.get(code=PlanCode.FREE)
            ent.pro_activated_at = None
        ent.save()
    return ent


def remaining_runs(ent: Entitlement) -> int:
    used = ent.task_runs_consumed + ent.task_runs_reserved
    return max(0, ent.plan.task_run_limit - used)


def remaining_sms(ent: Entitlement) -> int:
    return max(0, ent.plan.sms_limit - ent.sms_consumed)


@transaction.atomic
def reserve_run(user: User, *, task_id: int | None, reason: str = "work_start") -> bool:
    ent = ensure_entitlement(user)
    if remaining_runs(ent) <= 0:
        return False
    ent.task_runs_reserved += 1
    ent.save(update_fields=["task_runs_reserved"])
    AllowanceLedger.objects.create(user=user, task_id=task_id, action="reserve", reason=reason)
    return True


@transaction.atomic
def consume_run(user: User, *, task_id: int | None, reason: str = "deliverable") -> None:
    ent = ensure_entitlement(user)
    if ent.task_runs_reserved > 0:
        ent.task_runs_reserved -= 1
    ent.task_runs_consumed += 1
    ent.save(update_fields=["task_runs_reserved", "task_runs_consumed"])
    AllowanceLedger.objects.create(user=user, task_id=task_id, action="consume", reason=reason)


@transaction.atomic
def restore_run(user: User, *, task_id: int | None, reason: str) -> None:
    ent = ensure_entitlement(user)
    if ent.task_runs_reserved > 0:
        ent.task_runs_reserved -= 1
    ent.task_runs_restored += 1
    ent.save(update_fields=["task_runs_reserved", "task_runs_restored"])
    AllowanceLedger.objects.create(user=user, task_id=task_id, action="restore", reason=reason)


@transaction.atomic
def consume_sms(user: User) -> bool:
    ent = ensure_entitlement(user)
    if remaining_sms(ent) <= 0:
        return False
    ent.sms_consumed += 1
    ent.save(update_fields=["sms_consumed"])
    AllowanceLedger.objects.create(user=user, action="sms", reason="transactional_sms")
    return True


def serialize_entitlement(user: User) -> dict:
    ent = ensure_entitlement(user)
    return {
        "plan": ent.plan.code,
        "plan_name_fa": ent.plan.name_fa,
        "price_amount": str(ent.plan.price_amount),
        "price_unit": ent.plan.price_unit,
        "price_display_fa": "۲۹۹٬۰۰۰ تومان / ۳۰ روز" if ent.plan.code == PlanCode.PRO else "رایگان",
        "period_start": ent.period_start.isoformat(),
        "period_end": ent.period_end.isoformat(),
        "task_run_limit": ent.plan.task_run_limit,
        "task_runs_remaining": remaining_runs(ent),
        "task_runs_consumed": ent.task_runs_consumed,
        "task_runs_reserved": ent.task_runs_reserved,
        "sms_limit": ent.plan.sms_limit,
        "sms_remaining": remaining_sms(ent),
        "auto_renew": False,
    }
