# Generated by Django 5.1.1 on 2024-09-26 14:35

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("books", "0013_alter_books_co_authors"),
    ]

    operations = [
        migrations.CreateModel(
            name="PlagiarismCheckerLogs",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(blank=True, null=True)),
                ("results", models.JSONField(default=dict)),
                (
                    "book",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="books_checked",
                        to="books.books",
                    ),
                ),
                (
                    "chapter",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="book_chapter_checked",
                        to="books.bookschapter",
                    ),
                ),
            ],
            options={
                "verbose_name": "Plagiarism Checker Logs",
                "verbose_name_plural": "Plagiarism Checker Logs",
                "db_table": "plagiarism_checker_logs",
            },
        ),
    ]