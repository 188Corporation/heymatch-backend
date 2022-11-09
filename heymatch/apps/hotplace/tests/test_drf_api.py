import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

pytestmark = pytest.mark.django_db
User = get_user_model()


# class TestSearchHotPlaceViewSets:
#     """
#     Test Cases for
#     >>> from heymatch.apps.search.api.views import HotPlaceViewSet
#     >>> from heymatch.apps.search.api.views import HotPlaceActiveGroupViewSet
#     """
#
#     def test_list_200_if_no_hotplace(self, active_user: User, rc: RequestsClient):
#         # request
#         request = rc.get("/api/search/hotplace/")
#         # response
#         list_view = HotPlaceViewSet.as_view({"get": "list"})
#         response = list_view(request)
#         # test
#         assert response.status_code == 200
#         assert response.data == []  # empty
#
#     def test_list_200_if_hotplace_exists(
#         self, hotplaces: Sequence[HotPlace], active_user: User, ac: APIClient
#     ):
#         # request
#         ac.login(username='lauren', password='secret')
#         request: WSGIRequest = ac.get("/api/search/hotplace/", format="json")
#         # response
#         list_view = HotPlaceViewSet.as_view({"get": "list"})
#         response: Response = list_view(request)
#         # test
#         assert response.status_code == 200
#         assert response.data == {}
#
#     # def test_retrieve(self, user: User, rf: APIRequestFactory):
#     #     request = rf.get("/fake-url/")
#     #     request.user = AnonymousUser()
#     #
#     #     response = user_detail_view(request, username=user.username)
#     #     login_url = reverse(settings.LOGIN_URL)
#     #
#     #     assert isinstance(response, HttpResponseRedirect)
#     #     assert response.status_code == 302
#     #     assert response.url == f"{login_url}?next=/fake-url/"


@pytest.mark.skip
class AccountTests(APITestCase):
    """
    Test Cases for
    >>> from heymatch.apps.hotplace.api.views import HotPlaceViewSet
    >>> from heymatch.apps.hotplace.api.views import HotPlaceActiveGroupViewSet
    """

    def setUp(self) -> None:
        # self.auth_client =
        # authentication_header = {
        #     'Authorization': 'jwt ' + token
        # }
        return

    # def test_list_200_if_no_hotplace(self):
    #     """
    #     Ensure we can create a new account object.
    #     """
    #     url = reverse("api:search:search-hotplace-list")
    #
    #     response = self.client.get(url)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
