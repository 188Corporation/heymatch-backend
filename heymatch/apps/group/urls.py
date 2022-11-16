from django.urls import path

from heymatch.apps.group.api.views import GroupDetailViewSet, GroupsGenericViewSet

app_name = "group"

group_list_create_view = GroupsGenericViewSet.as_view({"get": "list", "post": "create"})
group_detail_view = GroupDetailViewSet.as_view({"get": "retrieve", "delete": "destroy"})

urlpatterns = [
    path("", group_list_create_view, name="group-list-create"),
    path("<int:group_id>/", group_detail_view, name="group-detail"),
]
