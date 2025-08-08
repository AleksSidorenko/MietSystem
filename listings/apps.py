# listings/apps.py
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ListingsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "listings"
    # verbose_name = _("Listings")

    def ready(self):
        import listings.translation
        import listings.signals

