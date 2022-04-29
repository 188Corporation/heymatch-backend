from django.urls import path

from heythere.apps.search.api.views import HotPlaceViewSet

app_name = "search"

hotplace_list = HotPlaceViewSet.as_view({"get": "list"})
hotplace_detail = HotPlaceViewSet.as_view({"get": "retrieve"})

urlpatterns = [
    # HotPlace Search
    path("hotplace/", hotplace_list, name="search-hotplace-list"),
    path("hotplace/<int:id>/", hotplace_detail, name="search-hotplace-detail"),
]
