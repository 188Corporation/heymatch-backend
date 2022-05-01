from typing import Sequence

import pytest
from django.db.models import Avg

from heythere.apps.group.models import Group
from heythere.apps.user.models import User

pytestmark = pytest.mark.django_db


# Test Cases for Group model methods
def test_active_group_has_member_number(active_groups: Sequence[Group]):
    user_manager = User.active_objects
    for group in active_groups:
        assert group.member_number is not None
        assert type(group.member_number) == int
        assert user_manager.count_group_members(group) == group.member_number
        # finally, validity of the date
        qs = User.objects.filter(is_active=True, joined_group__id=group.id)
        assert qs.count() == group.member_number


def test_active_group_has_member_avg_age(active_groups: Sequence[Group]):
    user_manager = User.active_objects
    for group in active_groups:
        assert group.member_avg_age is not None
        assert type(group.member_avg_age) == int
        assert user_manager.count_group_members_avg_age(group) == group.member_avg_age
        # finally, validity of the date
        avg_age = int(
            User.objects.filter(is_active=True, joined_group__id=group.id).aggregate(
                Avg("age")
            )["age__avg"]
        )
        assert avg_age == group.member_avg_age
