from django.core.management.base import BaseCommand

from apps.billing.services import seed_plans
from apps.coverage.seed import seed_capabilities


class Command(BaseCommand):
    help = "Seed sandbox capabilities and billing plans."

    def handle(self, *args, **options):
        seed_capabilities()
        seed_plans()
        self.stdout.write(self.style.SUCCESS("Seeded capabilities and plans (sandbox)."))
