# listings/forms.py

from django import forms
from listings.models import Listing


class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        # Добавьте все переводимые поля
        fields = [
            "title_en",
            "title_de",
            "title_ru",
            "description_en",
            "description_de",
            "description_ru",
            "address",
            "city",
            "country",
            "price_per_night",
            "rooms",
            "property_type",
            "amenities",
            "is_active",
            "user", # <-- Добавлено, если это поле используется в админке
        ]
        widgets = {
            "amenities": forms.CheckboxSelectMultiple,
        }