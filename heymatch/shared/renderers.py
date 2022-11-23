from django.http import JsonResponse
from rest_framework.renderers import JSONRenderer


class JSONResponseRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        status_code = renderer_context["response"].status_code
        response = {
            "status": "success",
            "code": status_code,
            "data": data,
            "message": None,
        }

        if not str(status_code).startswith("2"):
            response["status"] = "error"
            response["data"] = None
            try:
                response["message"] = data["detail"]
            except (KeyError, TypeError):
                response["data"] = data
        return super(JSONResponseRenderer, self).render(
            response, accepted_media_type, renderer_context
        )


class ErrorHandlerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    @staticmethod
    def process_exception(request, exception):
        """
        All exceptions (including Server Error 500) will be rendered as JSON
        """
        status_code = 500
        status_msg = "서버에서 예상하지 못한 에러가 발생했어요! 잠시 후 다시 시도해주세요."
        if hasattr(exception, "status_code"):
            status_code = int(exception.status_code)
        if hasattr(exception, "default_detail"):
            status_msg = str(exception.default_detail)
        return JsonResponse(
            data={
                "status": "error",
                "code": status_code,
                "data": None,
                "message": status_msg,
            }
        )
