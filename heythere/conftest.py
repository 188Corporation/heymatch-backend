from random import randint
from typing import Sequence

import pytest
from rest_framework.test import APIClient, APIRequestFactory, RequestsClient

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
from heythere.utils.util import generate_rand_geoopt_within_boundary


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
    return generate_real_groups(hotplace_name=RANDOM_HOTPLACE_NAMES[0], is_active=True)


@pytest.fixture
def hotplace() -> HotPlace:
    return generate_real_hotplace(hotplace_name=RANDOM_HOTPLACE_NAMES[0])


@pytest.fixture
def hotplaces() -> Sequence[HotPlace]:
    return generate_real_hotplaces()


@pytest.fixture
def rf() -> APIRequestFactory:
    return APIRequestFactory()


@pytest.fixture
def ac() -> APIClient:
    return APIClient()


@pytest.fixture
def rc() -> RequestsClient:
    return RequestsClient()


# ------ Generation Function ------ #
def generate_superuser(**kwargs) -> User:
    return AdminUserFactory.create(**kwargs)


def generate_inactive_users() -> Sequence[User]:
    return UserFactory.create_batch(size=randint(2, 5), is_active=False)


def generate_active_users() -> Sequence[User]:
    return UserFactory.create_batch(size=randint(2, 5), is_active=True)


def generate_real_group(hotplace_name: str, is_active: bool) -> Group:
    """
    Real-world Geo-location Group within specific Hotplace
    :return: Sequence[Group]
    """
    geopt = generate_rand_geoopt_within_boundary(
        RANDOM_HOTPLACE_INFO[hotplace_name]["zone_boundary_geoinfos"]
    )
    users = generate_active_users()
    return ActiveGroupFactory(
        members=users, gps_geo_location=geopt, is_active=is_active
    )


def generate_real_groups(hotplace_name: str, is_active: bool) -> Sequence[Group]:
    """
    Real-world Geo-location Group within All Hotplaces
    :return: Sequence[Group]
    """
    result = []
    for _ in range(5):
        group = generate_real_group(hotplace_name=hotplace_name, is_active=is_active)
        result.append(group)
    return result


def generate_real_hotplace(hotplace_name: str) -> HotPlace:
    groups = generate_real_groups(hotplace_name=hotplace_name, is_active=True)
    return HotPlaceFactory(
        groups=groups,
        name=hotplace_name,
        zone_center_geoinfo=RANDOM_HOTPLACE_INFO[hotplace_name]["zone_center_geoinfo"],
        zone_boundary_geoinfos=RANDOM_HOTPLACE_INFO[hotplace_name][
            "zone_boundary_geoinfos"
        ],
    )


def generate_real_hotplaces() -> Sequence[HotPlace]:
    """
    Real-world Geo-location Hotplaces
    Calling Fixture function directly is deprecated.
    :return: Sequence[HotPlace]
    """
    result = []
    for name in RANDOM_HOTPLACE_NAMES:
        hotplace = generate_real_hotplace(name)
        result.append(hotplace)
    return result
