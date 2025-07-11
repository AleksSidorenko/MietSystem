### locations/translation.py

from modeltranslation.translator import TranslationOptions, register

from locations.models import Location


# @register(Location, key='locations')
@register(Location)
class LocationTranslationOptions(TranslationOptions):
    fields = ("city", "federal_state")
