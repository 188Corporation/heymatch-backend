from random import randint
from typing import Sequence

import pytest

from heythere.apps.group.models import Group
from heythere.apps.group.tests.factories import ActiveGroupFactory
from heythere.apps.search.models import HotPlace
from heythere.apps.search.tests.factories import (
    RANDOM_HOTPLACE_INFO,
    RANDOM_HOTPLACE_NAMES,
    HotPlaceFactory,
)
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
    return UserFactory.create_batch(size=5, is_active=True)


@pytest.fixture
def active_group() -> Group:
    users = UserFactory.create_batch(size=randint(2, 5), is_active=True)
    return ActiveGroupFactory(members=users, is_active=True)


@pytest.fixture
def active_groups() -> Sequence[Group]:
    return generate_active_groups()


@pytest.fixture
def hotplace() -> HotPlace:
    users = UserFactory.create_batch(size=randint(2, 5), is_active=True)
    groups = ActiveGroupFactory(members=users, is_active=True)
    return HotPlaceFactory(groups=groups)


@pytest.fixture
def hotplaces() -> Sequence[HotPlace]:
    return generate_hotplaces()


# ------ Normal Function ------ #
def generate_superuser(**kwargs) -> User:
    return AdminUserFactory(**kwargs)


def generate_inactive_users() -> Sequence[User]:
    return UserFactory.create_batch(size=5, is_active=False)


def generate_active_users() -> Sequence[User]:
    return UserFactory.create_batch(size=5, is_active=True)


def generate_inactive_groups() -> Sequence[Group]:
    """
    Calling Fixture function directly is deprecated. So decided to make
    ordinary function to achieve brevity of codes.
    :return: Sequence[Group]
    """
    result = []
    for _ in range(5):
        users = UserFactory.create_batch(size=randint(2, 5), is_active=True)
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
        users = UserFactory.create_batch(size=randint(2, 5), is_active=True)
        result.append(ActiveGroupFactory(members=users, is_active=True))
    return result


def generate_hotplaces() -> Sequence[HotPlace]:
    """
    Calling Fixture function directly is deprecated.
    :return: Sequence[HotPlace]
    """
    result = []
    for name in RANDOM_HOTPLACE_NAMES:
        groups = generate_active_groups()
        result.append(HotPlaceFactory(groups=groups, name=name))
    return result


def generate_real_hotplaces() -> Sequence[HotPlace]:
    """
    Real-world Geo-location Hotplaces
    Calling Fixture function directly is deprecated.
    :return: Sequence[HotPlace]
    """
    result = []
    for name in RANDOM_HOTPLACE_NAMES:
        groups = generate_active_groups()
        result.append(
            HotPlaceFactory(
                groups=groups,
                name=name,
                zone_center_geoinfo=RANDOM_HOTPLACE_INFO[name]["zone_center_geoinfo"],
                zone_boundary_geoinfos=RANDOM_HOTPLACE_INFO[name][
                    "zone_boundary_geoinfos"
                ],
            )
        )
    return result
