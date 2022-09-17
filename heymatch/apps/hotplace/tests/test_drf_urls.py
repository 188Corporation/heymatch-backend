import pytest
from django.urls import resolve, reverse

from heymatch.apps.group.models import Group
from heymatch.apps.hotplace.models import HotPlace

pytestmark = pytest.mark.django_db


def test_hotplace_list():
    assert reverse("api:hotplace:hotplace-list") == "/api/hotplaces/"
    assert resolve("/api/hotplaces/").view_name == "api:hotplace:hotplace-list"


def test_hotplace_detail(hotplace: HotPlace):
    assert (
        reverse("api:hotplace:hotplace-detail", kwargs={"hotplace_id": hotplace.id})
        == f"/api/hotplaces/{hotplace.id}/"
    )
    assert (
        resolve(f"/api/hotplaces/{hotplace.id}/").view_name
        == "api:hotplace:hotplace-detail"
    )


def test_hotplace_group_list(hotplace: HotPlace):
    assert (
        reverse("api:hotplace:hotplace-group-list", kwargs={"hotplace_id": hotplace.id})
        == f"/api/hotplaces/{hotplace.id}/group/"
    )
    assert (
        resolve(f"/api/hotplaces/{hotplace.id}/group/").view_name
        == "api:hotplace:hotplace-group-list"
    )


def test_hotplace_group_detail(active_group: Group):
    hotplace = active_group.hotplace
    assert (
        reverse(
            "api:hotplace:hotplace-group-detail",
            kwargs={"hotplace_id": hotplace.id, "group_id": active_group.id},
        )
        == f"/api/hotplaces/{hotplace.id}/group/{active_group.id}/"
    )
    assert (
        resolve(f"/api/hotplaces/{hotplace.id}/group/{active_group.id}/").view_name
        == "api:hotplace:hotplace-group-detail"
    )
