from django.urls import path

from heythere.apps.search.api.views import HotPlaceActiveGroupViewSet, HotPlaceViewSet

app_name = "search"

hotplace_list = HotPlaceViewSet.as_view({"get": "list"})
hotplace_detail = HotPlaceViewSet.as_view({"get": "retrieve"})
hotplace_group_list = HotPlaceActiveGroupViewSet.as_view({"get": "list"})
hotplace_group_detail = HotPlaceActiveGroupViewSet.as_view({"get": "retrieve"})

urlpatterns = [
    # HotPlace Search
    path("hotplace/", hotplace_list, name="search-hotplace-list"),
    path("hotplace/<int:hotplace_id>/", hotplace_detail, name="search-hotplace-detail"),
    path(
        "hotplace/<int:hotplace_id>/group/",
        hotplace_group_list,
        name="search-hotplace-group-list",
    ),
    path(
        "hotplace/<int:hotplace_id>/group/<int:group_id>/",
        hotplace_group_detail,
        name="search-hotplace-group-detail",
    ),
]
