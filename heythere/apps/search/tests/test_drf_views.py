from typing import Sequence

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory

from heythere.apps.search.api.views import HotPlaceViewSet
from heythere.apps.search.models import HotPlace

pytestmark = pytest.mark.django_db
User = get_user_model()


class TestSearchHotPlaceViewSets:
    """
    Test Cases for
    >>> from heythere.apps.search.api.views import HotPlaceViewSet
    >>> from heythere.apps.search.api.views import HotPlaceActiveGroupViewSet
    """

    def test_list_403_if_no_hotplace(self, active_user: User, rf: APIRequestFactory):
        list_view = HotPlaceViewSet.as_view({"get": "list"})

        # Make an authenticated request to the view...
        request = rf.get("/api/search/hotplace/", user=active_user)
        response = list_view(request)
        assert response.status_code == 200

    def test_list_200_if_hotplace_exists(
        self, hotplaces: Sequence[HotPlace], rf: APIRequestFactory
    ):
        list_view = HotPlaceViewSet.as_view({"get": "list"})

        # Make an authenticated request to the view...
        request = rf.get("/search/hotplace/")
        response = list_view(request)
        assert response.status_code == 200

    # def test_retrieve(self, user: User, rf: APIRequestFactory):
    #     request = rf.get("/fake-url/")
    #     request.user = AnonymousUser()
    #
    #     response = user_detail_view(request, username=user.username)
    #     login_url = reverse(settings.LOGIN_URL)
    #
    #     assert isinstance(response, HttpResponseRedirect)
    #     assert response.status_code == 302
    #     assert response.url == f"{login_url}?next=/fake-url/"
