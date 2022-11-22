from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from heymatch.shared.renderers import server_error

urlpatterns = [
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # API base url
    path("api/", include("config.api_router")),
]

if settings.DEBUG or settings.ENABLE_DEBUG_TOOLBAR:
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]

if settings.ENABLE_DOCS:
    if "drf_yasg" in settings.INSTALLED_APPS:
        from django.conf.urls import url
        from drf_yasg import openapi
        from drf_yasg.views import get_schema_view
        from rest_framework import permissions

        schema_view = get_schema_view(
            openapi.Info(
                title="Hey There API Swagger",
                default_version="v0.0.1",
                description="Hey There API Swagger",
                terms_of_service="https://www.google.com/policies/terms/",
                contact=openapi.Contact(email="david.jeong0724@gmail.com"),
                license=openapi.License(name="BSD License"),
            ),
            public=True,
            permission_classes=(permissions.AllowAny,),
        )

        docs_urlpatterns = [
            url(
                r"^swagger/$",
                schema_view.with_ui("swagger", cache_timeout=0),
                name="schema-swagger-ui",
            ),
        ]

        urlpatterns += [path(r"docs/", include(docs_urlpatterns))]

handler500 = server_error
