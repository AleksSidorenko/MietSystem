### `reviews/models.py`

from django.db import models
from django.utils.translation import gettext_lazy as _
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
    # history = HistoricalRecords(excluded_fields=['comment'])
    landlord_response = models.TextField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["is_approved"], name="is_approved_idx"),
            models.Index(fields=["created_at"], name="created_at_idx"),
            models.Index(fields=["user", "is_approved"], name="user_approved_idx"),
        ]
        verbose_name = _("Review")
        # verbose_name_plural = _('Reviews')
        verbose_name_plural = "Reviews (Отзывы)"

    def __str__(self):
        return str(_(f"Review {self.id} - {self.booking.listing.title}"))


# from django.db import models
# from simple_history.models import HistoricalRecords
#
# class Review(models.Model):
#     user = models.ForeignKey('users.User', on_delete=models.CASCADE)
#     booking = models.OneToOneField('bookings.Booking', on_delete=models.CASCADE)
#     rating = models.IntegerField()
#     comment = models.TextField()
#     is_approved = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)
#     history = HistoricalRecords()
#
#     class Meta:
#         indexes = [
#             models.Index(fields=['is_approved'], name='is_approved_idx'),
#             models.Index(fields=['created_at'], name='created_at_idx'),
#         ]
#
#     def __str__(self):
#         return f"Review {self.id} - {self.booking.listing.title}"
