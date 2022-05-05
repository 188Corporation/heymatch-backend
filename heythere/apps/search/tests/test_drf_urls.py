import pytest
from django.urls import resolve, reverse

from heythere.apps.group.models import Group
from heythere.apps.search.models import HotPlace

pytestmark = pytest.mark.django_db


def test_search_hotplace_list():
    assert reverse("api:search:search-hotplace-list") == "/api/search/hotplace/"
    assert (
        resolve("/api/search/hotplace/").view_name == "api:search:search-hotplace-list"
    )


def test_search_hotplace_detail(hotplace: HotPlace):
    assert (
        reverse(
            "api:search:search-hotplace-detail", kwargs={"hotplace_id": hotplace.id}
        )
        == f"/api/search/hotplace/{hotplace.id}/"
    )
    assert (
        resolve(f"/api/search/hotplace/{hotplace.id}/").view_name
        == "api:search:search-hotplace-detail"
    )


def test_search_hotplace_group_list(hotplace: HotPlace):
    assert (
        reverse(
            "api:search:search-hotplace-group-list", kwargs={"hotplace_id": hotplace.id}
        )
        == f"/api/search/hotplace/{hotplace.id}/group/"
    )
    assert (
        resolve(f"/api/search/hotplace/{hotplace.id}/group/").view_name
        == "api:search:search-hotplace-group-list"
    )


def test_search_hotplace_group_detail(active_group: Group):
    hotplace = active_group.hotplace
    assert (
        reverse(
            "api:search:search-hotplace-group-detail",
            kwargs={"hotplace_id": hotplace.id, "group_id": active_group.id},
        )
        == f"/api/search/hotplace/{hotplace.id}/group/{active_group.id}/"
    )
    assert (
        resolve(
            f"/api/search/hotplace/{hotplace.id}/group/{active_group.id}/"
        ).view_name
        == "api:search:search-hotplace-group-detail"
    )
