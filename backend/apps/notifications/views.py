from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.notifications.models import Notification
from apps.notifications.services import serialize_notification


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def inbox(request: Request) -> Response:
    qs = Notification.objects.filter(user=request.user, channel="inbox")
    return Response({"notifications": [serialize_notification(n) for n in qs[:100]]})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_read(request: Request, pk: int) -> Response:
    n = Notification.objects.filter(id=pk, user=request.user).first()
    if not n:
        return Response({"error": "یافت نشد"}, status=404)
    n.read_at = timezone.now()
    n.save(update_fields=["read_at"])
    return Response(serialize_notification(n))
