from typing import Sequence

import pytest
from django.db.models import Avg

from heythere.apps.group.models import Group
from heythere.apps.user.models import User

pytestmark = pytest.mark.django_db


# Test Cases for Group model methods
def test_active_group_has_member_number(
    active_group: Group, active_users: Sequence[User]
):
    group_manager = Group.active_objects
    user_manager = User.active_objects
    group_manager.register_users(active_group, active_users)

    assert active_group.member_number is not None
    assert type(active_group.member_number) == int
    assert user_manager.count_group_members(active_group) == active_group.member_number
    # finally, validity of the date
    qs = User.objects.filter(is_active=True, joined_group__id=active_group.id)
    assert qs.count() == active_group.member_number


def test_active_group_has_member_avg_age(
    active_group: Group, active_users: Sequence[User]
):
    group_manager = Group.active_objects
    user_manager = User.active_objects
    group_manager.register_users(active_group, active_users)

    assert active_group.member_avg_age is not None
    assert type(active_group.member_avg_age) == int
    assert (
        user_manager.count_group_members_avg_age(active_group)
        == active_group.member_avg_age
    )
    # finally, validity of the date
    avg_age = int(
        User.objects.filter(is_active=True, joined_group__id=active_group.id).aggregate(
            Avg("age")
        )["age__avg"]
    )
    assert avg_age == active_group.member_avg_age


def test_active_group_manager_methods(
    active_group: Group, active_users: Sequence[User]
):
    """
    Test Methods:
     >>> from heythere.apps.group.managers import ActiveGroupManager
     >>> ActiveGroupManager.register_users()
    """
    #
    # -- All active
    group_manager = Group.active_objects
    group_manager.register_users(active_group, active_users)
    for user in active_users:
        assert user.joined_group == active_group

    # -- Make on inactive
    user = active_users[0]
    user.is_active = False
    user.save()
    with pytest.raises(RuntimeError):
        group_manager.register_users(active_group, active_users)
    assert user.joined_group is None
