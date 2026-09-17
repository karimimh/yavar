from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.memory.models import SavedFact


def _ser(f: SavedFact) -> dict:
    return {
        "id": f.id,
        "kind": f.kind,
        "label": f.label,
        "value": f.value,
        "origin_fa": f.origin_fa,
        "updated_at": f.updated_at.isoformat(),
    }


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def facts(request: Request) -> Response:
    if request.method == "GET":
        qs = SavedFact.objects.filter(user=request.user)
        return Response({"facts": [_ser(f) for f in qs]})
    data = request.data or {}
    if not data.get("save_for_future"):
        return Response({"ok": True, "saved": False, "used_for_task_only": True})
    fact = SavedFact.objects.create(
        user=request.user,
        kind=data.get("kind", "fact"),
        label=data.get("label", ""),
        value=data.get("value", ""),
        origin_fa=data.get("origin_fa") or "واردشده توسط کاربر",
    )
    return Response({"ok": True, "saved": True, "fact": _ser(fact)})


@api_view(["POST", "DELETE"])
@permission_classes([IsAuthenticated])
def fact_detail(request: Request, pk: int) -> Response:
    fact = SavedFact.objects.filter(id=pk, user=request.user).first()
    if not fact:
        return Response({"error": "یافت نشد"}, status=404)
    if request.method == "DELETE":
        fact.delete()
        return Response({"ok": True})
    for field in ("label", "value", "origin_fa"):
        if field in request.data:
            setattr(fact, field, request.data[field])
    fact.save()
    return Response(_ser(fact))
