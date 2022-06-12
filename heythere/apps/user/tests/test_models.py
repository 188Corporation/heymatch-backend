from statistics import mean
from typing import Sequence

import pytest

from heythere.apps.group.models import Group
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
    group = ActiveGroupFactory()
    manager = User.active_objects
    Group.objects.register_normal_users(group, active_users)

    assert active_users[0].joined_group == group
    left_ids = [str(user.id) for user in manager.get_group_members(group=group)]
    right_ids = [str(user.id) for user in active_users]
    assert set(left_ids) == set(right_ids)
    assert manager.count_group_members(group=group) == len(active_users)
    assert manager.count_group_members_avg_age(group=group) == int(
        mean([user.age for user in active_users])
    )
