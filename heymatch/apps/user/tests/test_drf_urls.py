import pytest
from django.urls import resolve, reverse

pytestmark = pytest.mark.django_db


# def test_user_detail(user: User):
#     assert (
#         reverse("api:user-detail", kwargs={"username": user.username})
#         == f"/api/users/{user.username}/"
#     )
#     assert resolve(f"/api/users/{user.username}/").view_name == "api:user-detail"
#     pass


def test_group_registration_status():
    assert reverse("api:user:user_my") == "/api/users/my/"
    assert resolve("/api/users/my/").view_name == "api:user:user_my"
