# bookings/models.py
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords
from decimal import Decimal, InvalidOperation


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        CONFIRMED = "CONFIRMED", _("Confirmed")
        CANCELLED = "CANCELLED", _("Cancelled")
        COMPLETED = "COMPLETED", _("Completed")  # <-- добавлено

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
        max_digits=10, decimal_places=2, verbose_name=_("Total price"), null=True
    )
    # total_price = models.DecimalField(
    #     max_digits=10, decimal_places=2, verbose_name=_("Total price"), null=False
    # )
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

    def __str__(self):
        return str(_(f"Booking {self.id} - {self.listing.title}"))

    def clean(self):
        # Валидация полей (вызывается full_clean)
        if self.end_date <= self.start_date:
            raise ValidationError(_("End date must be after start date"))
        # total_price может быть Decimal — для безопасности приводим к float/Decimal
        try:
            if self.total_price is not None and self.total_price < 0:
                raise ValidationError(_("Total price must be non-negative"))
        except TypeError:
            # Если total_price имеет неожиданный тип, бросим ValidationError
            raise ValidationError(_("Total price must be a number"))

    # def clean(self):
    #     if self.end_date <= self.start_date:
    #         raise ValidationError(_("End date must be after start date"))
    #     if self.total_price < 0:
    #         raise ValidationError(_("Total price must be non-negative"))

    def save(self, *args, **kwargs):
        """
        Если total_price не указан (None или пустая строка),
        автоматически вычисляем его как (end_date - start_date).days * listing.price_per_night.
        Не затираем total_price, если он явно задан (например, админом).
        Затем выполняем валидацию и сохраняем.
        """
        # Рассчитываем total_price, если он отсутствует/пуст
        try:
            needs_calc = self.total_price in (None, "", 0) and getattr(self, "start_date", None) and getattr(self, "end_date", None) and getattr(self, "listing", None)
        except Exception:
            needs_calc = False

        if needs_calc:
            try:
                duration_days = (self.end_date - self.start_date).days
                if duration_days <= 0:
                    # оставим расчётчик — clean() поймает ошибку про даты
                    self.total_price = Decimal("0.00")
                else:
                    price_per_night = getattr(self.listing, "price_per_night", None)
                    if price_per_night is None:
                        self.total_price = Decimal("0.00")
                    else:
                        # приводим к Decimal для безопасного умножения
                        self.total_price = Decimal(str(price_per_night)) * Decimal(duration_days)
            except Exception:
                # в случае какой-то ошибки ставим 0, чтобы не падать на NOT NULL
                self.total_price = Decimal("0.00")

        # Если total_price всё ещё None (маловероятно), ставим 0
        if self.total_price is None:
            self.total_price = Decimal("0.00")

        # Выполняем валидацию модели перед сохранением
        self.full_clean()
        super().save(*args, **kwargs)