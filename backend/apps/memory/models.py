from django.conf import settings
from django.db import models


class SavedFact(models.Model):
    KIND_CHOICES = (
        ("fact", "fact"),
        ("bill_alias", "bill_alias"),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_facts")
    kind = models.CharField(max_length=32, choices=KIND_CHOICES, default="fact")
    label = models.CharField(max_length=120)
    value = models.TextField()
    origin_fa = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["label"]
