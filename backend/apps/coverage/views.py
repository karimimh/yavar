from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from apps.coverage.models import Capability
from apps.coverage.seed import seed_capabilities
from apps.coverage.services import serialize_capability


@api_view(["GET"])
@permission_classes([AllowAny])
def capability_list(request: Request) -> Response:
    if not Capability.objects.exists():
        seed_capabilities()
    caps = Capability.objects.order_by("category", "slug")
    return Response(
        {
            "provider_mode": "sandbox",
            "disclaimer_fa": "همهٔ یکپارچه‌سازی‌های خارجی در حالت آزمایشی/سندباکس هستند و برند زندهٔ ایرانی ادعا نمی‌شود.",
            "capabilities": [serialize_capability(c) for c in caps],
        }
    )
