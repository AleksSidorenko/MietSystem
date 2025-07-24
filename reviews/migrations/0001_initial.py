# migrations/0001_initial.py

import django.db.models.deletion
import simple_history.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("bookings", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="HistoricalReview",
            fields=[
                (
                    "id",
                    models.BigIntegerField(
                        auto_created=True, blank=True, db_index=True, verbose_name="ID"
                    ),
                ),
                ("rating", models.IntegerField(verbose_name="Rating")),
                (
                    "is_approved",
                    models.BooleanField(default=False, verbose_name="Is approved"),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        blank=True, editable=False, verbose_name="Created at"
                    ),
                ),
                ("landlord_response", models.TextField(blank=True, null=True)),
                ("history_id", models.AutoField(primary_key=True, serialize=False)),
                ("history_date", models.DateTimeField(db_index=True)),
                ("history_change_reason", models.CharField(max_length=100, null=True)),
                (
                    "history_type",
                    models.CharField(
                        choices=[("+", "Created"), ("~", "Changed"), ("-", "Deleted")],
                        max_length=1,
                    ),
                ),
                (
                    "booking",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to="bookings.booking",
                        verbose_name="Booking",
                    ),
                ),
                (
                    "history_user",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="User",
                    ),
                ),
            ],
            options={
                "verbose_name": "historical Review",
                "verbose_name_plural": "historical Reviews (Отзывы)",
                "ordering": ("-history_date", "-history_id"),
                "get_latest_by": ("history_date", "history_id"),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name="Review",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("rating", models.IntegerField(verbose_name="Rating")),
                ("comment", models.TextField(verbose_name="Comment")),
                ("comment_en", models.TextField(null=True, verbose_name="Comment")),
                ("comment_de", models.TextField(null=True, verbose_name="Comment")),
                ("comment_ru", models.TextField(null=True, verbose_name="Comment")),
                (
                    "is_approved",
                    models.BooleanField(default=False, verbose_name="Is approved"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Created at"),
                ),
                ("landlord_response", models.TextField(blank=True, null=True)),
                (
                    "booking",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="review",
                        to="bookings.booking",
                        verbose_name="Booking",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reviews",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="User",
                    ),
                ),
            ],
            options={
                "verbose_name": "Review",
                "verbose_name_plural": "Reviews (Отзывы)",
                "indexes": [
                    models.Index(fields=["is_approved"], name="is_approved_idx"),
                    models.Index(fields=["created_at"], name="created_at_idx"),
                    models.Index(
                        fields=["user", "is_approved"], name="user_approved_idx"
                    ),
                ],
            },
        ),
    ]
