from django.urls import path

from heymatch.apps.group.api.views import (
    GroupDetailViewSet,
    GroupReportViewSet,
    GroupsGenericViewSet,
    GroupsTopAddressViewSet,
    V1GroupsGenericViewSet,
)

app_name = "group"

group_list_create_view = GroupsGenericViewSet.as_view(
    {"get": "list", "post": "create", "put": "update"}
)
group_top_address_list_view = GroupsTopAddressViewSet.as_view({"get": "retrieve"})

# DEPRECATED
v1_group_list_create_view = V1GroupsGenericViewSet.as_view(
    {"get": "list", "post": "create"}
)
group_detail_view = GroupDetailViewSet.as_view(
    {"get": "retrieve", "delete": "destroy", "put": "update"}
)
group_report_view = GroupReportViewSet.as_view({"post": "report"})

urlpatterns = [
    path("", group_list_create_view, name="group-list-create"),
    path(
        "top-ranked-address/",
        group_top_address_list_view,
        name="group-top-address-get",
    )
    # path("<int:group_id>/", group_detail_view, name="group-detail"),
    # path("<int:group_id>/report/", group_report_view, name="group-report"),
]
