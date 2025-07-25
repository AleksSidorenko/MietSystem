### reviews/apps.py

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ReviewsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "reviews"
    # verbose_name = _("Reviews")

    def ready(self):
        import reviews.signals
        import reviews.translation
