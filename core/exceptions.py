# core/exceptions.py
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    # Обычная обработка DRF
    response = exception_handler(exc, context)

    # Возвращаем, как есть — CustomRenderer обернёт в {"errors": ...}
    return response
