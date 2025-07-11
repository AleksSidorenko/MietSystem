### `bookings/models.py`

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        CONFIRMED = "CONFIRMED", _("Confirmed")
        CANCELLED = "CANCELLED", _("Cancelled")

    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="bookings",
        verbose_name=_("User"),
    )
    listing = models.ForeignKey(
        "listings.Listing",
        on_delete=models.CASCADE,
        related_name="bookings",
        verbose_name=_("Listing"),
    )
    start_date = models.DateField(verbose_name=_("Start date"))
    end_date = models.DateField(verbose_name=_("End date"))
    total_price = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Total price"), null=False
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name=_("Status"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    history = HistoricalRecords()

    class Meta:
        indexes = [
            models.Index(fields=["status"], name="status_idx"),
            models.Index(fields=["start_date"], name="start_date_idx"),
            models.Index(fields=["end_date"], name="end_date_idx"),
            models.Index(fields=["listing", "status"], name="listing_status_idx"),
        ]
        verbose_name = _("Booking")
        # verbose_name_plural = _('Bookings')
        verbose_name_plural = "Bookings (Бронирование)"

    def clean(self):
        if self.end_date <= self.start_date:
            raise ValidationError(_("End date must be after start date"))
        if self.total_price < 0:
            raise ValidationError(_("Total price must be non-negative"))

    def __str__(self):
        return str(_(f"Booking {self.id} - {self.listing.title}"))
