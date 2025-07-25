# Generated by Django 5.0 on 2025-07-10 10:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("analytics", "0002_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="historicalsearchhistory",
            options={
                "get_latest_by": ("history_date", "history_id"),
                "ordering": ("-history_date", "-history_id"),
                "verbose_name": "historical Search History",
                "verbose_name_plural": "historical Search Histories (История поисков)",
            },
        ),
        migrations.AlterModelOptions(
            name="historicalviewhistory",
            options={
                "get_latest_by": ("history_date", "history_id"),
                "ordering": ("-history_date", "-history_id"),
                "verbose_name": "historical View History",
                "verbose_name_plural": "historical View Histories (История просмотров)",
            },
        ),
        migrations.AlterModelOptions(
            name="searchhistory",
            options={
                "verbose_name": "Search History",
                "verbose_name_plural": "Search Histories (История поисков)",
            },
        ),
        migrations.AlterModelOptions(
            name="viewhistory",
            options={
                "verbose_name": "View History",
                "verbose_name_plural": "View Histories (История просмотров)",
            },
        ),
    ]
