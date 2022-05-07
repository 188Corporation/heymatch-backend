from django.urls import include, path

urlpatterns = [
    # rest-auth
    path("", include("rest_auth.urls")),
    path("signup/", include("rest_auth.registration.urls")),
    # GPS Auth
    path(
        "gps/authenticate/group/<int:group_id>",
        "TODO",
    ),
]
