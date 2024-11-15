# Generated by Django 5.1.1 on 2024-09-25 14:31

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("books", "0012_rename_co_author_books_co_authors"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="books",
            name="co_authors",
            field=models.ManyToManyField(
                blank=True, related_name="books_co_author", to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
