from random import randint
from typing import Sequence

import pytest
from rest_framework.test import APIClient

from heymatch.apps.group.models import Group
from heymatch.apps.group.tests.factories import ActiveGroupFactory, InactiveGroupFactory
from heymatch.apps.hotplace.models import HotPlace
from heymatch.apps.hotplace.tests.factories import (
    RANDOM_HOTPLACE_INFO,
    RANDOM_HOTPLACE_NAMES,
    HotPlaceFactory,
)
from heymatch.apps.match.models import MatchRequest
from heymatch.apps.match.tests.factories import MatchRequestFactory
from heymatch.apps.user.models import User
from heymatch.apps.user.tests.factories import (
    ActiveUserFactory,
    AdminUserFactory,
    InactiveUserFactory,
)
from heymatch.utils.util import generate_rand_geoopt_within_boundary


# ----- Fixtures ----- #
@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def admin_user() -> User:
    return AdminUserFactory()


@pytest.fixture
def active_user() -> User:
    return ActiveUserFactory()


@pytest.fixture
def inactive_user() -> User:
    return InactiveUserFactory()


@pytest.fixture
def active_users() -> Sequence[User]:
    return ActiveUserFactory.create_batch(size=randint(2, 4))


@pytest.fixture
def inactive_users() -> Sequence[User]:
    return InactiveUserFactory.create_batch(size=randint(2, 4))


@pytest.fixture
def active_groups_in_apgujeong() -> Sequence[Group]:
    hotplace_name = RANDOM_HOTPLACE_NAMES[0]
    hotplace = HotPlaceFactory(
        name=hotplace_name,
        zone_center_geoinfo=RANDOM_HOTPLACE_INFO[hotplace_name]["zone_center_geoinfo"],
        zone_boundary_geoinfos=RANDOM_HOTPLACE_INFO[hotplace_name][
            "zone_boundary_geoinfos"
        ],
    )
    geopt = generate_rand_geoopt_within_boundary(
        RANDOM_HOTPLACE_INFO[hotplace_name]["zone_boundary_geoinfos"]
    )
    return ActiveGroupFactory.create_batch(
        size=randint(5, 10),
        hotplace=hotplace,
        gps_geoinfo=geopt,
    )


@pytest.fixture
def active_group() -> Group:
    hotplace = HotPlaceFactory()
    return ActiveGroupFactory(hotplace=hotplace)


@pytest.fixture
def active_two_groups() -> Sequence[Group]:
    hotplace = HotPlaceFactory()
    return ActiveGroupFactory.create_batch(
        size=2,
        hotplace=hotplace,
    )


@pytest.fixture
def inactive_group() -> Group:
    hotplace = HotPlaceFactory()
    return InactiveGroupFactory(hotplace=hotplace)


@pytest.fixture
def active_groups_in_euljiro() -> Sequence[Group]:
    hotplace_name = RANDOM_HOTPLACE_NAMES[1]
    hotplace = HotPlaceFactory(
        name=hotplace_name,
        zone_center_geoinfo=RANDOM_HOTPLACE_INFO[hotplace_name]["zone_center_geoinfo"],
        zone_boundary_geoinfos=RANDOM_HOTPLACE_INFO[hotplace_name][
            "zone_boundary_geoinfos"
        ],
    )
    geopt = generate_rand_geoopt_within_boundary(
        RANDOM_HOTPLACE_INFO[hotplace_name]["zone_boundary_geoinfos"]
    )
    return ActiveGroupFactory.create_batch(
        size=randint(5, 10),
        hotplace=hotplace,
        gps_geoinfo=geopt,
    )


@pytest.fixture
def active_groups_in_hongdae() -> Sequence[Group]:
    hotplace_name = RANDOM_HOTPLACE_NAMES[2]
    hotplace = HotPlaceFactory(
        name=hotplace_name,
        zone_center_geoinfo=RANDOM_HOTPLACE_INFO[hotplace_name]["zone_center_geoinfo"],
        zone_boundary_geoinfos=RANDOM_HOTPLACE_INFO[hotplace_name][
            "zone_boundary_geoinfos"
        ],
    )
    geopt = generate_rand_geoopt_within_boundary(
        RANDOM_HOTPLACE_INFO[hotplace_name]["zone_boundary_geoinfos"]
    )
    return ActiveGroupFactory.create_batch(
        size=randint(5, 10),
        hotplace=hotplace,
        gps_geoinfo=geopt,
    )


@pytest.fixture
def hotplace_apgujeong() -> HotPlace:
    hotplace_name = RANDOM_HOTPLACE_NAMES[0]
    return HotPlaceFactory(
        name=hotplace_name,
        zone_center_geoinfo=RANDOM_HOTPLACE_INFO[hotplace_name]["zone_center_geoinfo"],
        zone_boundary_geoinfos=RANDOM_HOTPLACE_INFO[hotplace_name][
            "zone_boundary_geoinfos"
        ],
    )


@pytest.fixture
def hotplace_euljiro() -> HotPlace:
    hotplace_name = RANDOM_HOTPLACE_NAMES[1]
    return HotPlaceFactory(
        name=hotplace_name,
        zone_center_geoinfo=RANDOM_HOTPLACE_INFO[hotplace_name]["zone_center_geoinfo"],
        zone_boundary_geoinfos=RANDOM_HOTPLACE_INFO[hotplace_name][
            "zone_boundary_geoinfos"
        ],
    )


@pytest.fixture
def hotplace_hongdae() -> HotPlace:
    hotplace_name = RANDOM_HOTPLACE_NAMES[2]
    return HotPlaceFactory(
        name=hotplace_name,
        zone_center_geoinfo=RANDOM_HOTPLACE_INFO[hotplace_name]["zone_center_geoinfo"],
        zone_boundary_geoinfos=RANDOM_HOTPLACE_INFO[hotplace_name][
            "zone_boundary_geoinfos"
        ],
    )


@pytest.fixture
def hotplace() -> HotPlace:
    return HotPlaceFactory()


@pytest.fixture
def hotplaces() -> Sequence[HotPlace]:
    result = []
    for name in RANDOM_HOTPLACE_NAMES:
        hotplace = HotPlaceFactory(
            name=name,
            zone_center_geoinfo=RANDOM_HOTPLACE_INFO[name]["zone_center_geoinfo"],
            zone_boundary_geoinfos=RANDOM_HOTPLACE_INFO[name]["zone_boundary_geoinfos"],
        )
        result.append(hotplace)
    return result


@pytest.fixture
def match_request() -> MatchRequest:
    hotplace = HotPlaceFactory()
    sender = ActiveGroupFactory(hotplace=hotplace)
    receiver = ActiveGroupFactory(hotplace=hotplace)
    return MatchRequestFactory(sender=sender, receiver=receiver)


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


# ========================
#  DEPRECATED
# ========================
#
# @pytest.fixture
# def active_group_invitation_code() -> GroupInvitationCode:
#     return ActiveGroupInvitationCodeFactory()
#
