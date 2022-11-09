import pytest
from django.urls import resolve, reverse

pytestmark = pytest.mark.django_db


def test_user_detail():
    assert reverse("api:user:user-my-detail") == "/api/users/my/"
    assert resolve("/api/users/my/").view_name == "api:user:user-my-detail"
