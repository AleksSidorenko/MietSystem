### `core/middleware.py`

from rest_framework.response import Response


class MetaResponseMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if isinstance(response, Response) and response.status_code == 200:
            data = response.data
            if isinstance(data, list):
                meta = {"total_results": len(data), "page": 1}
            else:
                meta = {"total_results": 1, "page": 1}
            response.data = {"data": data, "meta": meta}
        return response
