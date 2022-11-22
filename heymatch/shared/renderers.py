from django.http import JsonResponse
from rest_framework import status
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


def server_error(request, *args, **kwargs):
    """
    Generic 500 error handler.
    """
    print("hihihihihi")
    data = {"error": "Server Error (500)"}
    return JsonResponse(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
