import pytest

from heythere.apps.users.models import User

pytestmark = pytest.mark.django_db


def test_user_detail(user: User):
    # assert (
    #     reverse("api:user-detail", kwargs={"username": user.username})
    #     == f"/api/users/{user.username}/"
    # )
    # assert resolve(f"/api/users/{user.username}/").view_name == "api:user-detail"
    pass
