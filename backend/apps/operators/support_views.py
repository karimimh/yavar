from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.operators.models import SupportIncident
from apps.tasks.models import Task


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def report_issue(request: Request) -> Response:
    data = request.data or {}
    task = None
    if data.get("task_id"):
        task = Task.objects.filter(id=data["task_id"], user=request.user).first()
        if not task:
            return Response({"error": "کار متعلق به شما نیست."}, status=403)
    consent = bool(data.get("consent_share_task"))
    context = {}
    if consent and task:
        context = {
            "task_id": task.id,
            "state": task.execution_state,
            "outcome": task.external_outcome,
            "title": task.title,
        }
    inc = SupportIncident.objects.create(
        reporter=request.user,
        task=task if consent else None,
        message=str(data.get("message", "")),
        consent_share_task=consent,
        redacted_context=context,
    )
    return Response({"ok": True, "incident_id": inc.id})
