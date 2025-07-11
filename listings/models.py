### `Project_MietSystem/listings/models.py`

from django.db import models
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords


class Amenity(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Amenity"))

    class Meta:
        verbose_name = _("Amenity")
        verbose_name_plural = "Amenities (Удобства)"

    def __str__(self):
        return self.name


class AvailabilitySlot(models.Model):
    listing = models.ForeignKey(
        "Listing",
        on_delete=models.CASCADE,
        related_name="availability_slots",
        verbose_name=_("Listing"),
    )
    date = models.DateField(verbose_name=_("Date"))
    is_available = models.BooleanField(default=True, verbose_name=_("Is Available"))

    class Meta:
        unique_together = ("listing", "date")
        indexes = [
            models.Index(fields=["listing", "date"]),
            models.Index(fields=["date"]),
        ]
        verbose_name = _("Availability Slot")
        verbose_name_plural = "Availability Slots (Интервалы доступности)"

    def __str__(self):
        return (
            f"{self.listing.title} – {self.date}: {'✓' if self.is_available else '✗'}"
        )


class Listing(models.Model):
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="listings"
    )
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    description = models.TextField(verbose_name=_("Description"))
    address = models.CharField(max_length=255, verbose_name=_("Address"))
    city = models.CharField(
        max_length=100, verbose_name=_("City"), blank=True, null=True
    )
    country = models.CharField(
        max_length=100, verbose_name=_("Country"), blank=True, null=True
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name=_("Latitude"),
        blank=True,
        null=True,
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name=_("Longitude"),
        blank=True,
        null=True,
    )
    price_per_night = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Price per night")
    )
    rooms = models.FloatField(verbose_name=_("Rooms"))

    class PropertyType(models.TextChoices):
        APARTMENT = "Apartment", _("Apartment")
        HOUSE = "House", _("House")
        STUDIO = "Studio", _("Studio")
        SHARED = "Shared Room", _("Shared Room")
        VILLA = "Villa", _("Villa")
        ONE_ROOM = "ONE_ROOM", _("One-Room Apartment")
        TWO_ROOM = "TWO_ROOM", _("Two-Room Apartment")
        THREE_ROOM = "THREE_ROOM", _("Three-Room Apartment")
        FOUR_ROOM = "FOUR_ROOM", _("Four-Room Apartment")
        DORMITORY = "Dormitory", _("Dormitory")
        PENTHOUSE = "Penthouse", _("Penthouse")
        TOWNHOUSE = "Townhouse", _("Townhouse")
        COTTAGE = "Cottage", _("Cottage")
        CONDOMINIUM = "Condominium", _("Condominium")
        LOFT = "Loft", _("Loft")
        DUPLEX = "Duplex", _("Duplex")
        BUNGALOW = "Bungalow", _("Bungalow")

    property_type = models.CharField(
        max_length=50,
        choices=PropertyType.choices,
        verbose_name=_("Property type"),
        default=PropertyType.APARTMENT,
    )

    amenities = models.ManyToManyField(
        "Amenity", blank=True, verbose_name=_("Amenities")
    )

    photos = models.JSONField(default=list, verbose_name=_("Photos"))
    is_active = models.BooleanField(default=True, verbose_name=_("Is active"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    popularity = models.PositiveIntegerField(default=0, verbose_name=_("Popularity"))

    history = HistoricalRecords(
        excluded_fields=[
            "title_en",
            "title_de",
            "title_ru",
            "description_en",
            "description_de",
            "description_ru",
        ]
    )

    class Meta:
        indexes = [
            models.Index(fields=["is_active"], name="is_act_idx"),
            models.Index(fields=["price_per_night"], name="price_night_idx"),
            models.Index(fields=["created_at"], name="created_at__idx"),
            models.Index(fields=["title"], name="list_title_idx"),
            models.Index(fields=["popularity"], name="popularity_idx"),
            models.Index(fields=["city"], name="city_idx"),
            models.Index(fields=["country"], name="country_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["address", "user"], name="unique_address_user"
            )
        ]
        verbose_name = _("Listing")
        verbose_name_plural = "Listings (Объявления)"

    def __str__(self):
        return self.title
