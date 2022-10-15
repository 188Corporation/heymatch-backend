from typing import List, Sequence

import pytest
from django.db.models import Avg

from heymatch.apps.group.models import Group
from heymatch.apps.user.models import User

pytestmark = pytest.mark.django_db


# --------------------------
#  [Group] Model Test Codes
# --------------------------
def test_active_group_has_member_number(
    active_group: Group, active_users: Sequence[User]
):
    group_manager = Group.objects
    user_manager = User.active_objects
    group_manager.register_normal_users(active_group, active_users)

    assert active_group.member_number is not None
    assert type(active_group.member_number) == int
    assert user_manager.count_group_members(active_group) == active_group.member_number
    # finally, validity of the date
    qs = User.objects.filter(is_active=True, joined_group__id=active_group.id)
    assert qs.count() == active_group.member_number


def test_active_group_has_member_avg_age(
    active_group: Group, active_users: Sequence[User]
):
    group_manager = Group.objects
    user_manager = User.active_objects
    group_manager.register_normal_users(active_group, active_users)

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


def test_active_group_manager_register_user_when_all_good(
    active_group: Group, active_user: User
):
    """
    Test Methods:
     >>> from heymatch.apps.group.managers import GroupManager
     >>> GroupManager.register_user()
    """
    # -- All active
    group_manager = Group.objects
    user = group_manager.register_user(active_group, active_user, is_group_leader=False)
    assert user.joined_group == active_group
    assert user.is_group_leader is False


def test_active_group_manager_register_user_when_inactive(
    active_group: Group, active_user: User
):
    """
    Test Methods:
     >>> from heymatch.apps.group.managers import GroupManager
     >>> GroupManager.register_user()
    """
    group_manager = Group.objects
    # -- Make on inactive
    active_user.is_active = False
    active_user.save()
    with pytest.raises(RuntimeError):
        group_manager.register_user(active_group, active_user, is_group_leader=False)

    assert active_user.joined_group is None
    assert active_user.is_group_leader is False


def test_active_group_manager_register_user_when_group_leader(
    active_group: Group, active_user: User
):
    """
    Test Methods:
     >>> from heymatch.apps.group.managers import GroupManager
     >>> GroupManager.register_user()
    """
    group_manager = Group.objects
    # -- Make is_group_leader=True
    active_user.is_group_leader = True
    active_user.save()
    user = group_manager.register_user(active_group, active_user, is_group_leader=False)
    assert user.is_group_leader is False


def test_active_group_manager_register_group_leader_user_when_all_good(
    active_group: Group, active_user: User
):
    """
    Test Methods:
     >>> from heymatch.apps.group.managers import GroupManager
     >>> GroupManager.register_group_leader_user()
    """
    # -- All active
    group_manager = Group.objects
    user = group_manager.register_group_leader_user(active_group, active_user)
    assert user.joined_group == active_group
    assert user.is_group_leader is True


def test_active_group_manager_register_group_leader_user_when_inactive(
    active_group: Group, active_user: User
):
    """
    Test Methods:
     >>> from heymatch.apps.group.managers import GroupManager
     >>> GroupManager.register_group_leader_user()
    """
    group_manager = Group.objects
    # -- Make on inactive
    active_user.is_active = False
    active_user.save()
    with pytest.raises(RuntimeError):
        group_manager.register_group_leader_user(active_group, active_user)

    assert active_user.joined_group is None
    assert active_user.is_group_leader is False


def test_active_group_manager_register_normal_users_when_all_good(
    active_group: Group, active_users: Sequence[User]
):
    """
    Test Methods:
     >>> from heymatch.apps.group.managers import GroupManager
     >>> GroupManager.register_normal_users()
    """
    # -- All active
    group_manager = Group.objects
    users = group_manager.register_normal_users(active_group, active_users)
    for user in users:
        assert user.joined_group == active_group
        assert user.is_group_leader is False


def test_active_group_manager_register_normal_users_when_one_is_inactive(
    active_group: Group, active_users: List[User], inactive_user: User
):
    """
    Test Methods:
     >>> from heymatch.apps.group.managers import GroupManager
     >>> GroupManager.register_normal_users()
    """
    group_manager = Group.objects
    # Include active and inactive users
    all_users = active_users + [inactive_user]
    with pytest.raises(RuntimeError):
        group_manager.register_normal_users(active_group, all_users)

    # Check Roll-back strategy. If one of users fails, all users should
    # fall back to original state.
    for user in all_users:
        assert user.joined_group is None
        assert user.is_group_leader is False
