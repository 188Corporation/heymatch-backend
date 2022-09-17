from django.urls import path

from heymatch.apps.hotplace.api.views import HotPlaceActiveGroupViewSet, HotPlaceViewSet

app_name = "hotplace"

hotplace_list = HotPlaceViewSet.as_view({"get": "list"})
hotplace_detail = HotPlaceViewSet.as_view({"get": "retrieve"})
hotplace_group_list = HotPlaceActiveGroupViewSet.as_view({"get": "list"})
hotplace_group_detail = HotPlaceActiveGroupViewSet.as_view({"get": "retrieve"})

urlpatterns = [
    # HotPlace Search
    path("", hotplace_list, name="hotplace-list"),
    path("<int:hotplace_id>/", hotplace_detail, name="hotplace-detail"),
    path(
        "<int:hotplace_id>/group/",
        hotplace_group_list,
        name="hotplace-group-list",
    ),
    path(
        "<int:hotplace_id>/group/<int:group_id>/",
        hotplace_group_detail,
        name="hotplace-group-detail",
    ),
]
