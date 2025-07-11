# utils/translation.py

from django.utils.translation import get_language
from rest_framework import serializers


class TranslationSerializerMixin:
    """
    Автоматически возвращает перевод поля в текущей локали.
    Поля модели должны быть зарегистрированы в modeltranslation.
    """

    def to_representation(self, instance):
        data = super().to_representation(instance)
        lang = get_language()

        # Проверяем, какие поля модели зарегистрированы как переводимые
        translation_opts = getattr(
            instance.__class__, "_translation_modeltranslation_opts", None
        )

        if translation_opts:
            for field in translation_opts.fields:
                translated_field = f"{field}_{lang}"
                if translated_field in data:
                    data[field] = data.get(translated_field)

        return data
