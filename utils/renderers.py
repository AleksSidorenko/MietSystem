# utils/renderers.py

from rest_framework.renderers import JSONRenderer
from rest_framework.utils.serializer_helpers import ReturnDict, ReturnList


class CustomRenderer(JSONRenderer):
    """
    Кастомный рендер для обёртки всех ответов в формат:
    {
        "data": ...,
        "errors": ...,
        "meta": ...
    }
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response", None)
        request = renderer_context.get("request", None)

        # Статус ответа
        status_code = getattr(response, "status_code", 200)

        # Метаданные можно добавить по необходимости (например: pagination, запрос, время ответа)
        meta = {
            "status_code": status_code,
            "method": request.method if request else None,
            "path": request.path if request else None,
        }

        # Обработка ошибок
        if not str(status_code).startswith("2"):
            response_data = {
                "data": None,
                "errors": data,
                "meta": meta,
            }
        else:
            # Нормализуем формат: если data — это list или dict, заворачиваем как есть
            normalized_data = data
            if isinstance(data, (ReturnDict, ReturnList)):
                normalized_data = data
            elif data is None:
                normalized_data = {}
            response_data = {
                "data": normalized_data,
                "errors": None,
                "meta": meta,
            }

        return super().render(response_data, accepted_media_type, renderer_context)
