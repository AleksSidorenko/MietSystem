### `reviews/translation.py`

from modeltranslation.translator import TranslationOptions, register

from .models import Review


# @register(Review, key='reviews')
@register(Review)
class ReviewTranslationOptions(TranslationOptions):
    fields = ("comment",)
