### Project_MietSystem/locations/models.py

from enum import Enum

from django.contrib.gis.db import models as gis_models
from django.db import models
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords


class FederalState(Enum):
    BADEN_WURTTEMBERG = "Baden-Württemberg"
    BAYERN = "Bayern"
    BERLIN = "Berlin"
    BRANDENBURG = "Brandenburg"
    BREMEN = "Bremen"
    HAMBURG = "Hamburg"
    HESSEN = "Hessen"
    MECKLENBURG_VORPOMMERN = "Mecklenburg-Vorpommern"
    NIEDERSACHSEN = "Niedersachsen"
    NORDRHEIN_WESTFALEN = "Nordrhein-Westfalen"
    RHEINLAND_PFALZ = "Rheinland-Pfalz"
    SAARLAND = "Saarland"
    SACHSEN = "Sachsen"
    SACHSEN_ANHALT = "Sachsen-Anhalt"
    SCHLESWIG_HOLSTEIN = "Schleswig-Holstein"
    THURINGEN = "Thüringen"


class City(Enum):
    STUTTGART = "Stuttgart"  # Baden-Württemberg
    MUNICH = "Munich"  # Bayern
    BERLIN = "Berlin"  # Berlin
    POTSDAM = "Potsdam"  # Brandenburg
    BREMEN = "Bremen"  # Bremen
    HAMBURG = "Hamburg"  # Hamburg
    WIESBADEN = "Wiesbaden"  # Hessen
    SCHWERIN = "Schwerin"  # Mecklenburg-Vorpommern
    HANNOVER = "Hannover"  # Niedersachsen
    DUSSELDORF = "Düsseldorf"  # Nordrhein-Westfalen
    MAINZ = "Mainz"  # Rheinland-Pfalz
    SAARBRUCKEN = "Saarbrücken"  # Saarland
    DRESDEN = "Dresden"  # Sachsen
    MAGDEBURG = "Magdeburg"  # Sachsen-Anhalt
    KIEL = "Kiel"  # Schleswig-Holstein
    ERFURT = "Erfurt"  # Thüringen
    KÖLN = "Köln"  # Köln
    # COLOGNE = 'Cologne'  # Köln
    LEIPZIG = "Leipzig"  # Leipzig
    FRANKFURT = "Frankfurt"  # Frankfurt


class Location(models.Model):
    listing = models.ForeignKey(
        "listings.Listing", on_delete=models.CASCADE, related_name="locations"
    )
    coordinates = gis_models.PointField(
        verbose_name=_("Coordinates"), null=True, blank=True
    )
    federal_state = models.CharField(
        max_length=100, choices=[(f.value, f.value) for f in FederalState]
    )
    city = models.CharField(max_length=100, choices=[(c.value, c.value) for c in City])
    postal_code = models.CharField(max_length=10, blank=True)
    street = models.CharField(max_length=255, blank=True)

    # Исключаем динамически добавленные modeltranslation поля
    history = HistoricalRecords(
        excluded_fields=[
            "city_en",
            "city_de",
            "city_ru",  # Добавьте все языки, которые вы используете в settings.py
            "federal_state_en",
            "federal_state_de",
            "federal_state_ru",  # И здесь также
        ]
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["city", "federal_state"], name="location_city_state_idx"
            )
        ]
        verbose_name = _("Location")
        # verbose_name_plural = _('Locations')
        verbose_name_plural = "Locations (Локация)"

    def __str__(self):
        # Используйте атрибут поля, чтобы получить значение на текущем языке
        return f"{self.city}, {self.federal_state}"
