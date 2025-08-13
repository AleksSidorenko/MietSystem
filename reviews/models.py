# reviews/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from simple_history.models import HistoricalRecords


class Review(models.Model):
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name=_("User"),
    )
    booking = models.OneToOneField(
        "bookings.Booking",
        on_delete=models.CASCADE,
        related_name="review",
        verbose_name=_("Booking"),
    )
    rating = models.IntegerField(verbose_name=_("Rating"))
    comment = models.TextField(verbose_name=_("Comment"))
    is_approved = models.BooleanField(default=False, verbose_name=_("Is approved"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    history = HistoricalRecords(
        excluded_fields=["comment", "comment_en", "comment_de", "comment_ru"]
    )
    landlord_response = models.TextField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["is_approved"], name="is_approved_idx"),
            models.Index(fields=["created_at"], name="created_at_idx"),
            models.Index(fields=["user", "is_approved"], name="user_approved_idx"),
        ]
        verbose_name = _("Review")
        verbose_name_plural = "Reviews (Отзывы)"

    def __str__(self):
        return str(_(f"Review {self.id} - {self.booking.listing.title}"))

    def clean(self):
        super().clean()
        if self.rating < 1 or self.rating > 5:
            raise ValidationError({"rating": _("Rating must be between 1 and 5.")})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
