from __future__ import annotations

import hashlib

from django.core.files.uploadedfile import UploadedFile
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.agent.runtime import process_message
from apps.conversations.models import Attachment, Conversation, Message
from apps.tasks.state import serialize_task

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_BYTES = 10 * 1024 * 1024


def _validate_image(upload: UploadedFile) -> tuple[bytes, str] | tuple[None, str]:
    content_type = upload.content_type or ""
    if content_type not in ALLOWED_TYPES:
        return None, "فقط JPEG، PNG یا WebP تا ۱۰ مگابایت."
    data = upload.read()
    if len(data) > MAX_BYTES:
        return None, "حجم تصویر بیش از ۱۰ مگابایت است."
    try:
        from io import BytesIO

        from PIL import Image

        Image.open(BytesIO(data)).verify()
    except Exception:
        return None, "فایل تصویر معتبر نیست."
    return data, ""


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def conversations(request: Request) -> Response:
    if request.method == "GET":
        qs = Conversation.objects.filter(user=request.user, deleted_at__isnull=True)
        return Response(
            {
                "conversations": [
                    {"id": c.id, "title": c.title, "updated_at": c.updated_at.isoformat()} for c in qs
                ]
            }
        )
    conv = Conversation.objects.create(user=request.user, title="گفتگو")
    return Response({"id": conv.id, "title": conv.title})


@api_view(["GET", "DELETE"])
@permission_classes([IsAuthenticated])
def conversation_detail(request: Request, pk: int) -> Response:
    conv = Conversation.objects.filter(id=pk, user=request.user).first()
    if not conv:
        return Response({"error": "یافت نشد"}, status=404)
    if request.method == "DELETE":
        conv.deleted_at = timezone.now()
        conv.save(update_fields=["deleted_at"])
        return Response({"ok": True})
    from apps.agent.runtime import _messages

    tasks = [serialize_task(t) for t in conv.tasks.all()]
    return Response({"id": conv.id, "title": conv.title, "messages": _messages(conv), "tasks": tasks})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_message(request: Request) -> Response:
    text = str(request.data.get("text") or "")
    conversation_id = request.data.get("conversation_id")
    upload = request.FILES.get("screenshot")
    attachment = None
    duplicate = False
    if upload:
        data, err = _validate_image(upload)
        if err:
            return Response({"ok": False, "error": err}, status=400)
        digest = hashlib.sha256(data).hexdigest()
        previous = Attachment.objects.filter(user=request.user, sha256=digest).first()
        from django.core.files.base import ContentFile

        attachment = Attachment(
            user=request.user,
            content_type=upload.content_type or "image/jpeg",
            size_bytes=len(data),
            sha256=digest,
            duplicate_of=previous,
        )
        # Placeholder message required by FK — process_message reassigns.
        conv = Conversation.objects.filter(id=conversation_id, user=request.user).first() if conversation_id else None
        if conv is None:
            conv = Conversation.objects.create(user=request.user, title="گفتگو")
            conversation_id = conv.id
        tmp = Message.objects.create(conversation=conv, role="user", text=text or "[تصویر]")
        attachment.message = tmp
        attachment.file.save(upload.name or "shot.jpg", ContentFile(data), save=True)
        duplicate = previous is not None
        if not text.strip():
            text = ""
    result = process_message(
        request.user,
        text,
        conversation_id=int(conversation_id) if conversation_id else None,
        attachment=attachment,
    )
    if duplicate:
        result["duplicate_screenshot_warning_fa"] = (
            "این تصویر قبلاً بارگذاری شده؛ موارد تکراری بی‌صدا ساخته نمی‌شوند."
        )
    return Response(result)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def delete_message(request: Request, pk: int) -> Response:
    msg = Message.objects.filter(id=pk, conversation__user=request.user).first()
    if not msg:
        return Response({"error": "یافت نشد"}, status=404)
    msg.secret_redacted = True
    msg.text = "[حذف‌شده]"
    msg.save(update_fields=["secret_redacted", "text"])
    return Response({"ok": True})
