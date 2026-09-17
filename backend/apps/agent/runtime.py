from __future__ import annotations

from apps.accounts.models import User
from apps.agent.intent import extract_intents
from apps.agent.llm import IntentItem
from apps.billing.services import remaining_runs, reserve_run
from apps.conversations.models import Attachment, Conversation, Message
from apps.core.enums import ExecutionState, TaskKind
from apps.core.persian import looks_like_otp_or_secret
from apps.notifications.services import notify_inbox
from apps.tasks.models import Task
from apps.tasks.state import append_event, serialize_task, start_run, transition, work_expired

KIND_MAP = {
    "reminder": TaskKind.REMINDER,
    "personal": TaskKind.PERSONAL,
    "research": TaskKind.RESEARCH,
    "travel_search": TaskKind.TRAVEL_SEARCH,
    "bill_inquiry": TaskKind.BILL_INQUIRY,
    "service_request": TaskKind.SERVICE_REQUEST,
    "unsupported": TaskKind.UNSUPPORTED,
    "secret_warning": TaskKind.UNSUPPORTED,
    "extraction": TaskKind.EXTRACTION,
}


def get_or_create_conversation(user: User, conversation_id: int | None) -> Conversation:
    if conversation_id:
        conv = Conversation.objects.filter(id=conversation_id, user=user, deleted_at__isnull=True).first()
        if conv:
            return conv
    return Conversation.objects.create(user=user, title="گفتگو")


def create_task_from_intent(user: User, conversation: Conversation, item: IntentItem) -> Task:
    kind = KIND_MAP.get(item.kind, TaskKind.PERSONAL)
    deliverable = _deliverable_for(item)
    task = Task.objects.create(
        user=user,
        conversation=conversation,
        kind=kind,
        title=item.title[:300],
        original_goal=item.original,
        agreed_deliverable=deliverable,
        original_wording=item.original,
        constraints={"hard": item.hard_constraints, "soft": item.soft_preferences},
        plan_checklist=_plan_for(item),
        payload=item.payload,
        capability_slug=_capability_for(item),
        remaining_work="",
        current_activity_fa="در صف",
    )
    append_event(task, "created", "کار از روی درخواست ثبت شد.")
    return task


def _deliverable_for(item: IntentItem) -> str:
    return {
        "reminder": "ایجاد یادآور داخل برنامه با تاریخ و زمان مشخص",
        "research": "مقایسهٔ منبع‌دار آزمایشی با محدودیت‌های کاربر",
        "travel_search": "جستجوی پرواز داخلی سندباکس و در صورت انتخاب، آماده‌سازی تحویل به ارائه‌دهنده",
        "bill_inquiry": "استعلام قبض سندباکس و در صورت درخواست، آماده‌سازی پرداخت — نه پرداخت قطعی",
        "service_request": "پیش‌نویس و در صورت تأیید، ارسال درخواست غیرالزام‌آور سندباکس",
        "unsupported": "توضیح گام پشتیبانی‌نشده و پیشنهاد نتیجهٔ امن جزئی",
        "secret_warning": "هشدار و حذف رمز؛ بدون استفاده از رمز",
        "personal": "ثبت کار شخصی داخل برنامه",
        "extraction": "پیش‌نویس تعهدات استخراج‌شده برای بازبینی کاربر",
    }.get(item.kind, "پیگیری کار داخل برنامه")


def _plan_for(item: IntentItem) -> list[dict]:
    if item.kind == "reminder":
        return [{"fa": "ثبت یادآور", "needs_approval": False}]
    if item.kind == "travel_search":
        return [
            {"fa": "جستجوی دو منبع آزمایشی", "needs_approval": False},
            {"fa": "انتخاب پیشنهاد و بازبینی", "needs_approval": False},
            {"fa": "تحویل به ارائه‌دهنده — خرید با شماست", "needs_approval": False},
        ]
    if item.kind == "bill_inquiry":
        return [
            {"fa": "رضایت افشای شناسه", "needs_approval": True},
            {"fa": "استعلام", "needs_approval": False},
            {"fa": "تحویل پرداخت در صورت درخواست", "needs_approval": False},
        ]
    if item.kind == "service_request":
        return [
            {"fa": "پیش‌نویس", "needs_approval": False},
            {"fa": "رضایت انتقال فیلد در صورت ارسال زودهنگام", "needs_approval": True},
            {"fa": "تأیید ارسال", "needs_approval": True},
        ]
    if item.kind == "research":
        return [{"fa": "پژوهش منابع عمومی آزمایشی", "needs_approval": False}]
    return [{"fa": "ثبت", "needs_approval": False}]


def _capability_for(item: IntentItem) -> str:
    return {
        "research": "public_research",
        "travel_search": "flight_search_alpha",
        "bill_inquiry": "electricity_bill",
        "service_request": "local_service_request",
    }.get(item.kind, "")


def process_message(
    user: User,
    text: str,
    *,
    conversation_id: int | None = None,
    attachment: Attachment | None = None,
    now=None,
) -> dict:
    conversation = get_or_create_conversation(user, conversation_id)
    secret = looks_like_otp_or_secret(text)
    if attachment and attachment.message_id:
        msg = attachment.message
        msg.text = text or msg.text
        msg.contains_secret_warning = secret
        msg.save(update_fields=["text", "contains_secret_warning"])
    else:
        msg = Message.objects.create(
            conversation=conversation,
            role="user",
            text=text,
            contains_secret_warning=secret,
        )
    if attachment and attachment.message_id != msg.id:
        attachment.message = msg
        attachment.save(update_fields=["message"])

    if secret:
        assistant = (
            "رمز یکبارمصرف، کارت یا اطلاعات بانکی را در گفتگو وارد نکنید و استفاده نمی‌شود. "
            "می‌توانید این پیام را حذف کنید. ادامه فقط روی صفحهٔ خود ارائه‌دهنده است."
        )
        Message.objects.create(conversation=conversation, role="assistant", text=assistant)
        return {
            "conversation_id": conversation.id,
            "messages": _messages(conversation),
            "tasks": [],
            "secret_warning": True,
            "offer_delete": True,
        }

    intents = extract_intents(text)
    if intents.batch_proposal:
        assistant = (
            "در هر درخواست حداکثر سه کار همزمان پشتیبانی می‌شود. "
            "این سه مورد را انجام بدهم و بقیه را جدا بفرستید؟"
        )
        Message.objects.create(conversation=conversation, role="assistant", text=assistant)
        return {
            "conversation_id": conversation.id,
            "messages": _messages(conversation),
            "tasks": [],
            "batch_proposal": [i.original for i in intents.items],
            "leftover": intents.leftover,
        }

    from apps.billing.services import ensure_entitlement, serialize_entitlement

    ent = ensure_entitlement(user)
    remaining = remaining_runs(ent)
    tasks: list[Task] = []
    notes: list[str] = []

    if attachment and not text.strip():
        item = IntentItem(
            kind="extraction",
            title="استخراج از تصویر",
            original="[screenshot]",
            payload={"attachment_id": attachment.id},
        )
        intents.items = [item]

    for item in intents.items:
        task = create_task_from_intent(user, conversation, item)
        if remaining <= 0 and item.kind not in {"reminder", "personal", "secret_warning"}:
            # Reminders/manual still allowed subject to abuse limits — P0: in-app reminder is included.
            if item.kind not in {"reminder", "personal"}:
                transition(
                    task,
                    ExecutionState.BLOCKED,
                    activity_fa="سهمیهٔ اجرا تمام شده؛ مشاهده و توقف کارها همچنان ممکن است.",
                )
                notes.append("limit_reached")
                tasks.append(task)
                continue
        if item.kind not in {"reminder", "personal", "secret_warning"}:
            if reserve_run(user, task_id=task.id):
                task.allowance_reserved = True
                task.save(update_fields=["allowance_reserved"])
        execute_task(task, item, now=now)
        tasks.append(task)

    if not conversation.title and tasks:
        conversation.title = tasks[0].title[:80]
        conversation.save(update_fields=["title"])

    assistant_text = _assistant_summary(tasks, notes)
    Message.objects.create(conversation=conversation, role="assistant", text=assistant_text)
    return {
        "conversation_id": conversation.id,
        "messages": _messages(conversation),
        "tasks": [serialize_task(t) for t in tasks],
        "entitlement": serialize_entitlement(user),
        "duplicate_screenshot": bool(attachment and attachment.duplicate_of_id),
    }


def _messages(conversation: Conversation) -> list[dict]:
    return [
        {
            "id": m.id,
            "role": m.role,
            "text": m.text,
            "created_at": m.created_at.isoformat(),
            "contains_secret_warning": m.contains_secret_warning,
        }
        for m in conversation.messages.all()
    ]


def _assistant_summary(tasks: list[Task], notes: list[str]) -> str:
    if not tasks:
        return "درخواست ثبت شد."
    bits = []
    for t in tasks:
        bits.append(f"«{t.title}» — {t.current_activity_fa or t.execution_state}")
        if t.execution_state == ExecutionState.DELIVERED and t.kind in {
            TaskKind.TRAVEL_HANDOFF,
            TaskKind.BILL_HANDOFF,
            TaskKind.TRAVEL_SEARCH,
        }:
            bits.append("این فقط آماده‌سازی است، نه خرید یا پرداخت قطعی.")
    return "\n".join(bits)


def execute_task(task: Task, item: IntentItem | None = None, *, now=None) -> Task:
    """Python executes tools. The model cannot change registry, approvals, or mark external success."""
    from apps.agent import tools

    if task.stop_requested_at:
        return transition(task, ExecutionState.CANCELLED, activity_fa="متوقف شد")
    start_run(task)
    kind = item.kind if item else task.kind
    if kind == "reminder" or task.kind == TaskKind.REMINDER:
        return tools.run_reminder(task, item, now=now)
    if kind == "research" or task.kind == TaskKind.RESEARCH:
        return tools.run_research(task, item)
    if kind in {"travel_search", TaskKind.TRAVEL_SEARCH, TaskKind.TRAVEL_HANDOFF}:
        return tools.run_travel_search(task, item)
    if kind in {"bill_inquiry", TaskKind.BILL_INQUIRY, TaskKind.BILL_HANDOFF}:
        return tools.run_bill_inquiry(task, item)
    if kind in {"service_request", TaskKind.SERVICE_REQUEST}:
        return tools.run_service_draft(task, item)
    if kind in {"unsupported", "secret_warning", TaskKind.UNSUPPORTED}:
        return tools.run_unsupported(task, item)
    if kind in {"extraction", TaskKind.EXTRACTION}:
        return tools.run_extraction(task)
    transition(task, ExecutionState.DELIVERED, activity_fa="کار شخصی ثبت شد")
    return task


def continue_background(task_id: int) -> None:
    """Public research may continue after tab close within work limit. Approval-pending stays paused."""
    task = Task.objects.get(id=task_id)
    if task.execution_state == ExecutionState.NEEDS_APPROVAL:
        return
    if task.execution_state in {ExecutionState.NEEDS_INFORMATION, ExecutionState.NEEDS_USER_TAKEOVER}:
        return
    if work_expired(task):
        transition(task, ExecutionState.EXPIRED, activity_fa="محدودیت زمان کار؛ ادامه نیاز به تأیید شما دارد")
        notify_inbox(
            task.user,
            title_fa="کار ناتمام ماند",
            body_fa="یکی از کارهایت به توجه نیاز دارد",
            task=task,
        )
        return
    if task.kind == TaskKind.RESEARCH and task.execution_state in {
        ExecutionState.QUEUED,
        ExecutionState.IN_PROGRESS,
    }:
        from apps.agent import tools

        tools.run_research(task, None)
        notify_inbox(task.user, title_fa="مقایسه آماده است", body_fa="یکی از کارهایت آماده است", task=task, sms=True)
