from apps.core.enums import CapabilityStatus
from apps.coverage.models import Capability, OperatorSettings

CAPABILITIES = [
    {
        "slug": "public_research",
        "name_fa": "پژوهش و مقایسهٔ عمومی",
        "description_fa": "مقایسهٔ کالا، بستهٔ اینترنت و خدمات محلی از منابع عمومی آزمایشی.",
        "category": "research",
        "status": CapabilityStatus.LIMITED,
        "sandbox": True,
        "geography_note_fa": "منابع سندباکس؛ برند واقعی ایرانی ادعا نمی‌شود.",
        "required_user_steps_fa": "انتخاب گزینه و ادامه در سایت فروشنده در صورت نیاز.",
        "supports_handoff": True,
        "supports_submit": False,
    },
    {
        "slug": "flight_search_alpha",
        "name_fa": "جستجوی پرواز داخلی — منبع آلفا",
        "description_fa": "جستجوی پرواز یک‌طرفه، یک بزرگسال، اکونومی (سندباکس).",
        "category": "travel",
        "status": CapabilityStatus.LIMITED,
        "sandbox": True,
        "geography_note_fa": "مسیرهای آزمایشی داخلی.",
        "required_user_steps_fa": "هویت و خرید فقط در صفحهٔ ارائه‌دهنده.",
        "supports_handoff": True,
        "supports_submit": False,
    },
    {
        "slug": "flight_search_beta",
        "name_fa": "جستجوی پرواز داخلی — منبع بتا",
        "description_fa": "منبع دوم جستجو؛ بدون مسیر تحویل عمیق پایدار.",
        "category": "travel",
        "status": CapabilityStatus.LIMITED,
        "sandbox": True,
        "geography_note_fa": "مسیرهای آزمایشی داخلی.",
        "required_user_steps_fa": "پس از انتخاب ممکن است انتخاب مجدد در سایت لازم باشد.",
        "supports_handoff": False,
        "supports_submit": False,
    },
    {
        "slug": "electricity_bill",
        "name_fa": "استعلام قبض برق",
        "description_fa": "استعلام با شناسهٔ قبض و آماده‌سازی پرداخت (سندباکس).",
        "category": "bills",
        "status": CapabilityStatus.LIMITED,
        "sandbox": True,
        "geography_note_fa": "شناسهٔ آزمایشی ۱۰ رقمی؛ پوشش جغرافیایی سندباکس.",
        "required_user_steps_fa": "پرداخت فقط در صفحهٔ ارائه‌دهنده؛ کارت و رمز را در چت وارد نکنید.",
        "identifier_type": "bill_id_10",
        "supports_handoff": True,
        "supports_submit": False,
    },
    {
        "slug": "local_service_request",
        "name_fa": "درخواست خدمت محلی غیرالزام‌آور",
        "description_fa": "ارسال درخواست نوبت تعویض روغن آزمایشی بدون پیش‌پرداخت.",
        "category": "requests",
        "status": CapabilityStatus.LIMITED,
        "sandbox": True,
        "geography_note_fa": "فقط فرم سندباکس محلی.",
        "required_user_steps_fa": "تأیید دقیق فیلدها؛ نوبت قطعی نیست مگر ارائه‌دهنده صریحاً بپذیرد.",
        "supports_handoff": False,
        "supports_submit": True,
    },
]


def seed_capabilities() -> None:
    OperatorSettings.get()
    for item in CAPABILITIES:
        Capability.objects.update_or_create(slug=item["slug"], defaults=item)
