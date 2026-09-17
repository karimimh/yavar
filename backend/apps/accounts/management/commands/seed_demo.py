from django.core.management.base import BaseCommand

from apps.accounts.models import User
from apps.billing.services import ensure_entitlement
from apps.coverage.seed import seed_capabilities
from apps.memory.models import SavedFact


class Command(BaseCommand):
    help = "Create a clearly labeled demo user. Demo receipts must stay labeled آزمایشی."

    def handle(self, *args, **options):
        seed_capabilities()
        user, created = User.objects.get_or_create(
            phone="+989120000000",
            defaults={
                "phone_original": "09120000000",
                "preferred_name": "کاربر آزمایشی",
                "onboarding_completed_at": None,
            },
        )
        from django.utils import timezone

        user.preferred_name = "کاربر آزمایشی"
        user.timezone = "Asia/Tehran"
        user.terms_accepted_at = timezone.now()
        user.privacy_accepted_at = timezone.now()
        user.onboarding_completed_at = timezone.now()
        user.save()
        ensure_entitlement(user)
        SavedFact.objects.update_or_create(
            user=user,
            kind="bill_alias",
            label="برق خانه",
            defaults={"value": "THRHOME01", "origin_fa": "دادهٔ آزمایشی سندباکس"},
        )
        self.stdout.write(
            self.style.WARNING(
                "Demo user +989120000000 created. OTP still required unless you sign in via Django shell. "
                "All provider data is آزمایشی/sandbox."
            )
        )
