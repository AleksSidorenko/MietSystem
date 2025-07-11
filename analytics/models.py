### `analytics/models.py`

from django.db import models
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords


class SearchHistory(models.Model):
    user = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="search_history",
        verbose_name=_("User"),
    )
    query = models.CharField(max_length=255, verbose_name=_("Query"))
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_("Timestamp"))
    history = HistoricalRecords()

    class Meta:
        indexes = [
            models.Index(fields=["timestamp"], name="sh_ts_idx"),
            models.Index(fields=["user", "timestamp"], name="user_ts_idx"),
        ]
        verbose_name = _("Search History")
        verbose_name_plural = "Search Histories (История поисков)"
        # verbose_name_plural = _('Search Histories')

    def __str__(self):
        return str(_(f"Search: {self.query}"))


class ViewHistory(models.Model):
    user = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="view_history",
        verbose_name=_("User"),
    )
    listing = models.ForeignKey(
        "listings.Listing",
        on_delete=models.CASCADE,
        related_name="view_history",
        verbose_name=_("Listing"),
    )
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_("Timestamp"))
    history = HistoricalRecords()

    class Meta:
        indexes = [
            models.Index(fields=["timestamp"], name="vh_ts_idx"),
            models.Index(fields=["listing", "timestamp"], name="listing_ts_idx"),
        ]
        verbose_name = _("View History")
        verbose_name_plural = "View Histories (История просмотров)"
        # verbose_name_plural = _('View Histories')

    def __str__(self):
        return str(_(f"View: {self.listing.title}"))
