# Generated by Django 5.1.1 on 2024-11-05 13:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="analytics",
            options={"verbose_name": "Analytics", "verbose_name_plural": "Analytics"},
        ),
        migrations.AlterModelTable(
            name="analytics",
            table="analytics",
        ),
    ]
