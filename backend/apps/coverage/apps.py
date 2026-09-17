from django.apps import AppConfig


class CoverageConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.coverage"

    def ready(self) -> None:
        from django.db.models.signals import post_migrate

        def _seed(sender, **kwargs):
            from apps.billing.services import seed_plans
            from apps.coverage.seed import seed_capabilities

            seed_capabilities()
            seed_plans()

        post_migrate.connect(_seed, sender=self)
