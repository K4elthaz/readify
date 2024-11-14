# Generated by Django 5.1.1 on 2024-09-25 13:01

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("books", "0009_chapterunlockedbyuser"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="books",
            name="co_author",
            field=models.ManyToManyField(
                blank=True, null=True, to=settings.AUTH_USER_MODEL
            ),
        ),
    ]