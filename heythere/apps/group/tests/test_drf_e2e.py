import pytest
from rest_framework.test import APIClient

from heythere.apps.group.models import GroupInvitationCode
from heythere.apps.search.tests.factories import (
    RANDOM_HOTPLACE_INFO,
    RANDOM_HOTPLACE_NAMES,
)
from heythere.apps.user.models import User
from heythere.apps.user.tests.factories import ActiveUserFactory
from heythere.utils.util import generate_rand_geoopt_within_boundary

pytestmark = pytest.mark.django_db


class TestGroupRegistrationStatusEndpoints:
    ENDPOINT = "/api/group/registration/status/"

    def test_registration_status(self, api_client: APIClient):
        pass


class TestGroupRegistrationStep1Endpoints:
    STATUS_ENDPOINT = "/api/group/registration/status/"
    STEP_1_ENDPOINT = "/api/group/registration/step/1/"
    STEP_2_ENDPOINT = "/api/group/registration/step/2/"
    INVITATION_ENDPOINT = "/api/group/invitation-code/generate/"

    # -------------
    #  Step 1 Flow
    # -------------
    def test_registration_step_1_all_good(self, hotplaces, api_client):
        active_user = ActiveUserFactory(joined_group=None)
        api_client.force_authenticate(user=active_user)
        geoinfo = generate_rand_geoopt_within_boundary(
            RANDOM_HOTPLACE_INFO[RANDOM_HOTPLACE_NAMES[0]]["zone_boundary_geoinfos"]
        )
        res = api_client.post(
            self.STEP_1_ENDPOINT,
            data={"gps_geoinfo": geoinfo},
        )
        assert res.status_code == 201
        assert res.data["gps_checked"] is True
        assert res.data["register_step_1_completed"] is True

    def test_registration_step_1_if_unauthenticated(self, hotplaces, api_client):
        geoinfo = generate_rand_geoopt_within_boundary(
            RANDOM_HOTPLACE_INFO[RANDOM_HOTPLACE_NAMES[0]]["zone_boundary_geoinfos"]
        )
        res = api_client.post(
            self.STEP_1_ENDPOINT,
            data={"gps_geoinfo": geoinfo},
        )
        assert res.status_code == 401

    def test_registration_step_1_if_already_passed_step_1(self, hotplaces, api_client):
        active_user = ActiveUserFactory(joined_group=None)
        api_client.force_authenticate(user=active_user)
        geoinfo = generate_rand_geoopt_within_boundary(
            RANDOM_HOTPLACE_INFO[RANDOM_HOTPLACE_NAMES[0]]["zone_boundary_geoinfos"]
        )
        res = api_client.post(
            self.STEP_1_ENDPOINT,
            data={"gps_geoinfo": geoinfo},
        )
        assert res.status_code == 201

        # call again and fail
        res = api_client.post(
            self.STEP_1_ENDPOINT,
            data={"gps_geoinfo": geoinfo},
        )
        assert res.status_code == 403

    def test_registration_step_1_if_already_joined_group_and_not_leader(
        self, hotplaces, api_client
    ):
        active_user = ActiveUserFactory()
        # Case1: If not group leader
        api_client.force_authenticate(user=active_user)
        geoinfo = generate_rand_geoopt_within_boundary(
            RANDOM_HOTPLACE_INFO[RANDOM_HOTPLACE_NAMES[0]]["zone_boundary_geoinfos"]
        )
        res = api_client.post(
            self.STEP_1_ENDPOINT,
            data={"gps_geoinfo": geoinfo},
        )
        assert res.status_code == 403

    def test_registration_step_1_if_already_joined_group_and_leader(
        self, hotplaces, api_client
    ):
        active_user = ActiveUserFactory(is_group_leader=True)
        geoinfo = generate_rand_geoopt_within_boundary(
            RANDOM_HOTPLACE_INFO[RANDOM_HOTPLACE_NAMES[0]]["zone_boundary_geoinfos"]
        )
        api_client.force_authenticate(user=active_user)
        res = api_client.post(
            self.STEP_1_ENDPOINT,
            data={"gps_geoinfo": geoinfo},
        )
        assert res.status_code == 403

    def test_registration_step_1_geoinfo_not_in_hotplace(self, hotplaces, api_client):
        active_user = ActiveUserFactory(joined_group=None)
        api_client.force_authenticate(user=active_user)
        res = api_client.post(
            self.STEP_1_ENDPOINT,
            data={"gps_geoinfo": "20.123456,20.123456"},
        )
        assert res.status_code == 400

    # -------------
    #  Step 2 Flow
    # -------------
    def test_registration_step_2_all_good(self, hotplaces, api_client):
        # Group Leader calls Step 1
        active_user = ActiveUserFactory(joined_group=None)
        api_client.force_authenticate(user=active_user)
        geoinfo = generate_rand_geoopt_within_boundary(
            RANDOM_HOTPLACE_INFO[RANDOM_HOTPLACE_NAMES[0]]["zone_boundary_geoinfos"]
        )
        res = api_client.post(
            self.STEP_1_ENDPOINT,
            data={"gps_geoinfo": geoinfo},
        )
        assert res.status_code == 201

        # Friends get Group Invitation code for each
        friends = ActiveUserFactory.create_batch(size=3, joined_group=None)
        friends_codes = []
        for friend in friends:
            api_client.force_authenticate(user=friend)
            res = api_client.post(self.INVITATION_ENDPOINT)
            assert friend.joined_group is None
            assert res.status_code == 201
            friends_codes.append(res.data["code"])

        # Group Leader calls Step 2
        api_client.force_authenticate(user=active_user)
        res = api_client.post(
            self.STEP_2_ENDPOINT,
            data={"invitation_codes": friends_codes},
        )
        assert res.status_code == 200

        # Check if all friends joined group
        for friend in friends:
            code = GroupInvitationCode.objects.get(user=friend)
            f_obj = User.active_objects.get(id=friend.id)
            assert code.is_active is False
            assert f_obj.joined_group.id == active_user.joined_group.id

    def test_registration_step_2_if_unauthenticated(self, api_client):
        res = api_client.post(
            self.STEP_2_ENDPOINT,
            data={"invitation_codes": [1234]},
        )
        assert res.status_code == 401

    def test_registration_step_2_if_not_group_leader(self, api_client):
        active_user = ActiveUserFactory(joined_group=None)
        api_client.force_authenticate(user=active_user)
        res = api_client.post(
            self.STEP_2_ENDPOINT,
            data={"invitation_codes": [1234]},
        )
        assert res.status_code == 403

    def test_registration_step_2_if_not_completed_step_1(self, api_client):
        active_user = ActiveUserFactory(joined_group=None, is_group_leader=True)
        api_client.force_authenticate(user=active_user)

        # first generate invitation code
        friend = ActiveUserFactory.create(joined_group=None)
        api_client.force_authenticate(user=friend)
        res = api_client.post(self.INVITATION_ENDPOINT)
        assert res.status_code == 201

        # group leader calls
        api_client.force_authenticate(user=active_user)
        res = api_client.post(
            self.STEP_2_ENDPOINT,
            data={"invitation_codes": [res.data["code"]]},
        )
        assert res.status_code == 403

    def test_registration_step_2_if_any_invitation_code_is_invalid(
        self, hotplaces, api_client
    ):
        # Group Leader calls Step 1
        active_user = ActiveUserFactory(joined_group=None)
        api_client.force_authenticate(user=active_user)
        geoinfo = generate_rand_geoopt_within_boundary(
            RANDOM_HOTPLACE_INFO[RANDOM_HOTPLACE_NAMES[0]]["zone_boundary_geoinfos"]
        )
        res = api_client.post(
            self.STEP_1_ENDPOINT,
            data={"gps_geoinfo": geoinfo},
        )
        assert res.status_code == 201

        # Friends get Group Invitation code for each
        friends = ActiveUserFactory.create_batch(size=3, joined_group=None)
        friends_codes = []
        for friend in friends:
            api_client.force_authenticate(user=friend)
            res = api_client.post(self.INVITATION_ENDPOINT)
            assert friend.joined_group is None
            assert res.status_code == 201
            friends_codes.append(res.data["code"])

        # Add Fake code
        friends_codes.append(1111)

        # Group Leader calls Step 2
        api_client.force_authenticate(user=active_user)
        res = api_client.post(
            self.STEP_2_ENDPOINT,
            data={"invitation_codes": friends_codes},
        )
        assert res.status_code == 400

        # Check if all friends failed to join group
        for friend in friends:
            code = GroupInvitationCode.objects.get(user=friend)
            f_obj = User.active_objects.get(id=friend.id)
            assert code.is_active is True
            assert f_obj.joined_group is None

    # ----------------------
    #  Invitation Code Flow
    # ----------------------
    def test_invitation_code_generation(self, api_client):
        friend = ActiveUserFactory.create(joined_group=None)
        api_client.force_authenticate(user=friend)
        res = api_client.post(self.INVITATION_ENDPOINT)
        assert res.status_code == 201
