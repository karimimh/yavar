from django.db import migrations
from pgvector.django import VectorExtension


class Migration(migrations.Migration):
    """Enable the pgvector extension so it is available for future use."""

    initial = True

    dependencies = []

    operations = [VectorExtension()]
