from django.urls import include, path

app_name = "chat"

urlpatterns = [
    path("", include("django_messages_drf.urls", namespace="django_messages_drf")),
]
