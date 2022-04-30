import pytest

pytestmark = pytest.mark.django_db

# class TestUserViewSet:
#     def test_get_queryset(self, user: User, rf: RequestFactory):
#         view = UserViewSet()
#         request = rf.get("/fake-url/")
#         request.user = user
#
#         view.request = request
#
#         assert user in view.get_queryset()
#         pass
