from statistics import mean
from typing import Sequence

import pytest

from heythere.apps.group.tests.factories import ActiveGroupFactory
from heythere.apps.user.models import User
from heythere.utils.util import calculate_age_from_birthdate

pytestmark = pytest.mark.django_db


# Test Cases for User model methods
def test_user_calculate_age(active_user: User):
    assert active_user.age == calculate_age_from_birthdate(active_user.birthdate)


def test_user_has_age(active_users: Sequence[User]):
    for user in active_users:
        assert user.age is not None
        assert type(user.age) == int


# ActiveUserManager Test Cases
def test_active_user_manager_methods(active_users: Sequence[User]):
    group = ActiveGroupFactory(members=active_users, is_active=True)
    manager = User.active_objects

    assert active_users[0].joined_group == group
    assert list(manager.get_group_members(group=group)) == active_users
    assert manager.count_group_members(group=group) == len(active_users)
    assert manager.count_group_members_avg_age(group=group) == int(
        mean([user.age for user in active_users])
    )
