from django.urls import include, path

urlpatterns = [
    # dj-rest-auth
    path("", include("dj_rest_auth.urls")),
    path("signup/", include("dj_rest_auth.registration.urls")),
]
