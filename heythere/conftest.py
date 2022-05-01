from random import randint
from typing import Sequence

import pytest
from rest_framework.test import APIRequestFactory

from heythere.apps.group.models import Group
from heythere.apps.group.tests.factories import ActiveGroupFactory
from heythere.apps.search.models import HotPlace
from heythere.apps.search.tests.factories import RANDOM_HOTPLACE_NAMES, HotPlaceFactory
from heythere.apps.user.models import User
from heythere.apps.user.tests.factories import AdminUserFactory, UserFactory


# ----- Fixtures ----- #
@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def admin_user() -> User:
    return AdminUserFactory()


@pytest.fixture
def active_user() -> User:
    return UserFactory(is_active=True)


@pytest.fixture
def active_users() -> Sequence[User]:
    return generate_active_users()


@pytest.fixture
def active_group() -> Group:
    users = generate_active_users()
    return ActiveGroupFactory(members=users, is_active=True)


@pytest.fixture
def active_groups() -> Sequence[Group]:
    return generate_active_groups()


@pytest.fixture
def hotplace() -> HotPlace:
    return generate_hotplace()


@pytest.fixture
def hotplaces() -> Sequence[HotPlace]:
    return generate_hotplaces()


@pytest.fixture
def rf() -> APIRequestFactory:
    return APIRequestFactory()


# ------ Generation Function ------ #
def generate_superuser(**kwargs) -> User:
    return AdminUserFactory(**kwargs)


def generate_inactive_users() -> Sequence[User]:
    return UserFactory.create_batch(size=randint(2, 5), is_active=False)


def generate_active_users() -> Sequence[User]:
    return UserFactory.create_batch(size=randint(2, 5), is_active=True)


def generate_inactive_groups() -> Sequence[Group]:
    """
    Calling Fixture function directly is deprecated. So decided to make
    ordinary function to achieve brevity of codes.
    :return: Sequence[Group]
    """
    result = []
    for _ in range(5):
        users = generate_active_users()
        result.append(ActiveGroupFactory(members=users, is_active=False))
    return result


def generate_active_groups() -> Sequence[Group]:
    """
    Calling Fixture function directly is deprecated. So decided to make
    ordinary function to achieve brevity of codes.
    :return: Sequence[Group]
    """
    result = []
    for _ in range(5):
        users = generate_active_users()
        result.append(ActiveGroupFactory(members=users, is_active=True))
    return result


def generate_hotplace(**kwargs) -> HotPlace:
    groups = generate_active_groups()
    return HotPlaceFactory(groups=groups, **kwargs)


def generate_hotplaces() -> Sequence[HotPlace]:
    """
    Calling Fixture function directly is deprecated.
    :return: Sequence[HotPlace]
    """
    result = []
    for name in RANDOM_HOTPLACE_NAMES:
        result.append(generate_hotplace(name=name))
    return result
