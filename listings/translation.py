# Project_MietSystem/listings/translation.py

from modeltranslation.translator import TranslationOptions, register

from .models import Listing


@register(Listing)
class ListingTranslationOptions(TranslationOptions):
    fields = ("title", "description")
