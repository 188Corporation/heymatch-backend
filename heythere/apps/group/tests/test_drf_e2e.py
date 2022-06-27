import tempfile

import pytest
from PIL import Image
from rest_framework.test import APIClient

from heythere.apps.group.models import Group, GroupInvitationCode, GroupProfileImage
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

    def test_registration_status_all_good(self, api_client: APIClient):
        active_user = ActiveUserFactory(joined_group=None)
        api_client.force_authenticate(user=active_user)
        res = api_client.get(self.ENDPOINT)
        assert res.status_code == 200

    def test_registration_status_if_not_authenticated(self, api_client: APIClient):
        res = api_client.get(self.ENDPOINT)
        assert res.status_code == 401


class TestGroupRegistrationEndpoints:
    STATUS_ENDPOINT = "/api/group/registration/status/"
    STEP_1_ENDPOINT = "/api/group/registration/step/1/"
    STEP_2_ENDPOINT = "/api/group/registration/step/2/"
    STEP_3_ENDPOINT = "/api/group/registration/step/3/"
    STEP_4_ENDPOINT = "/api/group/registration/step/4/"
    STEP_CONFIRM_ENDPOINT = "/api/group/registration/step/confirm/"
    UNREGISTER_ENDPOINT = "/api/group/registration/unregister/"
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

        # Check if group is still inactive
        assert active_user.joined_group is not None
        assert active_user.joined_group.is_active is False
        assert active_user.joined_group.desired_other_group_member_number is None
        assert active_user.joined_group.desired_other_group_member_avg_age_range is None
        assert active_user.joined_group.register_step_1_completed is True
        assert active_user.joined_group.register_step_2_completed is False
        assert active_user.joined_group.register_step_3_completed is False
        assert active_user.joined_group.register_step_4_completed is False
        assert active_user.joined_group.register_step_all_confirmed is False

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
        assert active_user.joined_group is not None
        assert active_user.joined_group.is_active is False

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
        assert active_user.joined_group is not None
        assert active_user.joined_group.is_active is False

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
        assert active_user.joined_group is not None
        assert active_user.joined_group.is_active is False
        assert active_user.joined_group.desired_other_group_member_number is None
        assert active_user.joined_group.desired_other_group_member_avg_age_range is None
        assert active_user.joined_group.register_step_1_completed is True
        assert active_user.joined_group.register_step_2_completed is True
        assert active_user.joined_group.register_step_3_completed is False
        assert active_user.joined_group.register_step_4_completed is False
        assert active_user.joined_group.register_step_all_confirmed is False

        # Check if all friends joined group
        for friend in friends:
            code = GroupInvitationCode.objects.get(user=friend)
            f_obj = User.active_objects.get(id=friend.id)
            assert code.is_active is False
            assert f_obj.joined_group.id == active_user.joined_group.id
            assert f_obj.joined_group.is_active is False

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
        assert active_user.joined_group is None

    def test_registration_step_2_if_not_completed_step_1(self, api_client):
        active_user = ActiveUserFactory(joined_group=None)
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
        assert active_user.joined_group is None

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
        assert active_user.joined_group is not None
        assert active_user.joined_group.is_active is False
        assert active_user.joined_group.desired_other_group_member_number is None
        assert active_user.joined_group.desired_other_group_member_avg_age_range is None
        assert active_user.joined_group.register_step_1_completed is True
        assert active_user.joined_group.register_step_2_completed is False
        assert active_user.joined_group.register_step_3_completed is False
        assert active_user.joined_group.register_step_4_completed is False
        assert active_user.joined_group.register_step_all_confirmed is False

        # Check if all friends failed to join group
        for friend in friends:
            code = GroupInvitationCode.objects.get(user=friend)
            f_obj = User.active_objects.get(id=friend.id)
            assert code.is_active is True
            assert f_obj.joined_group is None

    # -------------
    #  Step 3 Flow
    # -------------
    def test_registration_step_3_all_good(self, hotplaces, api_client):
        active_user = ActiveUserFactory(joined_group=None)
        api_client.force_authenticate(user=active_user)

        # Do Step 1
        geoinfo = generate_rand_geoopt_within_boundary(
            RANDOM_HOTPLACE_INFO[RANDOM_HOTPLACE_NAMES[0]]["zone_boundary_geoinfos"]
        )
        res = api_client.post(
            self.STEP_1_ENDPOINT,
            data={"gps_geoinfo": geoinfo},
        )
        assert res.status_code == 201

        # Do step 2
        friends = ActiveUserFactory.create_batch(size=3, joined_group=None)
        friends_codes = []
        for friend in friends:
            api_client.force_authenticate(user=friend)
            res = api_client.post(self.INVITATION_ENDPOINT)
            assert res.status_code == 201
            friends_codes.append(res.data["code"])

        api_client.force_authenticate(user=active_user)
        res = api_client.post(
            self.STEP_2_ENDPOINT,
            data={"invitation_codes": friends_codes},
        )
        assert res.status_code == 200

        # Do Step 3
        # Create temp image file
        image = Image.new("RGBA", size=(50, 50), color=(155, 0, 0))
        file = tempfile.NamedTemporaryFile(suffix=".png")
        image.save(file)

        with open(file.name, "rb") as data:
            res = api_client.post(
                self.STEP_3_ENDPOINT,
                data={"image": data},
                format="multipart",
            )
            assert res.status_code == 200

        image = GroupProfileImage.objects.get(group=active_user.joined_group)
        assert image.image is not None
        assert image.image_blurred is not None
        assert image.thumbnail is not None
        assert image.thumbnail_blurred is not None

        assert active_user.joined_group is not None
        assert active_user.joined_group.is_active is False
        assert active_user.joined_group.desired_other_group_member_number is None
        assert active_user.joined_group.desired_other_group_member_avg_age_range is None
        assert active_user.joined_group.register_step_1_completed is True
        assert active_user.joined_group.register_step_2_completed is True
        assert active_user.joined_group.register_step_3_completed is True
        assert active_user.joined_group.register_step_4_completed is False
        assert active_user.joined_group.register_step_all_confirmed is False

    def test_registration_step_3_if_unauthenticated(self, api_client):
        # Do step 3
        image = Image.new("RGBA", size=(50, 50), color=(155, 0, 0))
        file = tempfile.NamedTemporaryFile(suffix=".png")
        image.save(file)

        with open(file.name, "rb") as data:
            res = api_client.post(
                self.STEP_3_ENDPOINT,
                data={"image": data},
                format="multipart",
            )
            assert res.status_code == 401

    def test_registration_step_3_if_not_group_leader(self, api_client):
        active_user = ActiveUserFactory(joined_group=None)
        api_client.force_authenticate(user=active_user)

        # Do step 3
        image = Image.new("RGBA", size=(50, 50), color=(155, 0, 0))
        file = tempfile.NamedTemporaryFile(suffix=".png")
        image.save(file)

        with open(file.name, "rb") as data:
            res = api_client.post(
                self.STEP_3_ENDPOINT,
                data={"image": data},
                format="multipart",
            )
        assert res.status_code == 403
        assert active_user.joined_group is None

    def test_registration_step_3_if_not_completed_step_1(self, api_client):
        active_user = ActiveUserFactory(joined_group=None)
        api_client.force_authenticate(user=active_user)

        # Do step 3
        image = Image.new("RGBA", size=(50, 50), color=(155, 0, 0))
        file = tempfile.NamedTemporaryFile(suffix=".png")
        image.save(file)

        with open(file.name, "rb") as data:
            res = api_client.post(
                self.STEP_3_ENDPOINT,
                data={"image": data},
                format="multipart",
            )
        assert res.status_code == 403
        assert active_user.joined_group is None

    def test_registration_step_3_if_not_completed_step_2(self, hotplaces, api_client):
        active_user = ActiveUserFactory(joined_group=None)
        api_client.force_authenticate(user=active_user)

        # Do step 1
        geoinfo = generate_rand_geoopt_within_boundary(
            RANDOM_HOTPLACE_INFO[RANDOM_HOTPLACE_NAMES[0]]["zone_boundary_geoinfos"]
        )
        res = api_client.post(
            self.STEP_1_ENDPOINT,
            data={"gps_geoinfo": geoinfo},
        )
        assert res.status_code == 201

        # Do step 3
        image = Image.new("RGBA", size=(50, 50), color=(155, 0, 0))
        file = tempfile.NamedTemporaryFile(suffix=".png")
        image.save(file)

        with open(file.name, "rb") as data:
            res = api_client.post(
                self.STEP_3_ENDPOINT,
                data={"image": data},
                format="multipart",
            )
        assert res.status_code == 403
        assert active_user.joined_group is not None
        assert active_user.joined_group.is_active is False
        assert active_user.joined_group.desired_other_group_member_number is None
        assert active_user.joined_group.desired_other_group_member_avg_age_range is None
        assert active_user.joined_group.register_step_1_completed is True
        assert active_user.joined_group.register_step_2_completed is False
        assert active_user.joined_group.register_step_3_completed is False
        assert active_user.joined_group.register_step_4_completed is False
        assert active_user.joined_group.register_step_all_confirmed is False

    def test_registration_step_3_if_file_format_is_wrong(self, hotplaces, api_client):
        active_user = ActiveUserFactory(joined_group=None)
        api_client.force_authenticate(user=active_user)

        # Do Step 1
        geoinfo = generate_rand_geoopt_within_boundary(
            RANDOM_HOTPLACE_INFO[RANDOM_HOTPLACE_NAMES[0]]["zone_boundary_geoinfos"]
        )
        res = api_client.post(
            self.STEP_1_ENDPOINT,
            data={"gps_geoinfo": geoinfo},
        )
        assert res.status_code == 201

        # Do step 2
        friends = ActiveUserFactory.create_batch(size=3, joined_group=None)
        friends_codes = []
        for friend in friends:
            api_client.force_authenticate(user=friend)
            res = api_client.post(self.INVITATION_ENDPOINT)
            assert res.status_code == 201
            friends_codes.append(res.data["code"])

        api_client.force_authenticate(user=active_user)
        res = api_client.post(
            self.STEP_2_ENDPOINT,
            data={"invitation_codes": friends_codes},
        )
        assert res.status_code == 200

        # Do Step 3
        # Create temp image file
        image = Image.new("RGBA", size=(50, 50), color=(155, 0, 0))
        file = tempfile.NamedTemporaryFile(suffix=".png")
        image.save(file)

        with open(file.name, "rb") as data:
            with pytest.raises(UnicodeDecodeError):
                api_client.post(
                    self.STEP_3_ENDPOINT,
                    data={"image": data},
                    format="json",
                )

        assert active_user.joined_group is not None
        assert active_user.joined_group.is_active is False
        assert active_user.joined_group.desired_other_group_member_number is None
        assert active_user.joined_group.desired_other_group_member_avg_age_range is None
        assert active_user.joined_group.register_step_1_completed is True
        assert active_user.joined_group.register_step_2_completed is True
        assert active_user.joined_group.register_step_3_completed is False
        assert active_user.joined_group.register_step_4_completed is False
        assert active_user.joined_group.register_step_all_confirmed is False

    def test_registration_step_3_patch_image_file(self, hotplaces, api_client):
        active_user = ActiveUserFactory(joined_group=None)
        api_client.force_authenticate(user=active_user)

        # Do Step 1
        geoinfo = generate_rand_geoopt_within_boundary(
            RANDOM_HOTPLACE_INFO[RANDOM_HOTPLACE_NAMES[0]]["zone_boundary_geoinfos"]
        )
        res = api_client.post(
            self.STEP_1_ENDPOINT,
            data={"gps_geoinfo": geoinfo},
        )
        assert res.status_code == 201

        # Do step 2
        friends = ActiveUserFactory.create_batch(size=3, joined_group=None)
        friends_codes = []
        for friend in friends:
            api_client.force_authenticate(user=friend)
            res = api_client.post(self.INVITATION_ENDPOINT)
            assert res.status_code == 201
            friends_codes.append(res.data["code"])

        api_client.force_authenticate(user=active_user)
        res = api_client.post(
            self.STEP_2_ENDPOINT,
            data={"invitation_codes": friends_codes},
        )
        assert res.status_code == 200

        # Do Step 3
        image = Image.new("RGBA", size=(50, 50), color=(155, 0, 0))
        file = tempfile.NamedTemporaryFile(suffix=".png")
        image.save(file)

        with open(file.name, "rb") as data:
            res = api_client.post(
                self.STEP_3_ENDPOINT,
                data={"image": data},
                format="multipart",
            )
            assert res.status_code == 200

        orig_image = GroupProfileImage.objects.get(group=active_user.joined_group)

        # Patch step 3
        image = Image.new("RGBA", size=(100, 100), color=(155, 155, 155))
        file = tempfile.NamedTemporaryFile(suffix=".png")
        image.save(file)

        with open(file.name, "rb") as data:
            res = api_client.patch(
                self.STEP_3_ENDPOINT,
                data={"image": data},
                format="multipart",
            )
            assert res.status_code == 200
            assert active_user.joined_group is not None
            assert active_user.joined_group.is_active is False
            assert active_user.joined_group.desired_other_group_member_number is None
            assert (
                active_user.joined_group.desired_other_group_member_avg_age_range
                is None
            )
            assert active_user.joined_group.register_step_1_completed is True
            assert active_user.joined_group.register_step_2_completed is True
            assert active_user.joined_group.register_step_3_completed is True
            assert active_user.joined_group.register_step_4_completed is False
            assert active_user.joined_group.register_step_all_confirmed is False

        updated_image = GroupProfileImage.objects.get(group=active_user.joined_group)

        # check if updated
        assert orig_image.image is not updated_image.image
        assert orig_image.image_blurred is not updated_image.image_blurred
        assert orig_image.thumbnail is not updated_image.thumbnail
        assert orig_image.thumbnail_blurred is not updated_image.thumbnail_blurred

    # -------------
    #  Step 4 Flow
    # -------------
    def test_registration_step_4_all_good(self, hotplaces, api_client):
        active_user = ActiveUserFactory(joined_group=None)
        api_client.force_authenticate(user=active_user)

        # Do Step 1
        geoinfo = generate_rand_geoopt_within_boundary(
            RANDOM_HOTPLACE_INFO[RANDOM_HOTPLACE_NAMES[0]]["zone_boundary_geoinfos"]
        )
        res = api_client.post(
            self.STEP_1_ENDPOINT,
            data={"gps_geoinfo": geoinfo},
        )
        assert res.status_code == 201

        # Do step 2
        friends = ActiveUserFactory.create_batch(size=3, joined_group=None)
        friends_codes = []
        for friend in friends:
            api_client.force_authenticate(user=friend)
            res = api_client.post(self.INVITATION_ENDPOINT)
            assert res.status_code == 201
            friends_codes.append(res.data["code"])

        api_client.force_authenticate(user=active_user)
        res = api_client.post(
            self.STEP_2_ENDPOINT,
            data={"invitation_codes": friends_codes},
        )
        assert res.status_code == 200

        # Do Step 3
        image = Image.new("RGBA", size=(50, 50), color=(155, 0, 0))
        file = tempfile.NamedTemporaryFile(suffix=".png")
        image.save(file)

        with open(file.name, "rb") as data:
            res = api_client.post(
                self.STEP_3_ENDPOINT,
                data={"image": data},
                format="multipart",
            )
            assert res.status_code == 200

        # Do Step 4
        orig_group = active_user.joined_group
        orig_title = orig_group.title
        orig_introduction = orig_group.introduction
        orig_desired_other_group_member_number = (
            orig_group.desired_other_group_member_number
        )
        orig_desired_other_group_member_avg_age_range = (
            orig_group.desired_other_group_member_avg_age_range
        )

        res = api_client.patch(
            self.STEP_4_ENDPOINT,
            data={
                "title": "test_title",
                "introduction": "test_introduction",
                "desired_other_group_member_number": 3,
                "desired_other_group_member_avg_age_range": [20, 28],
            },
        )
        assert res.status_code == 200
        assert active_user.joined_group is not None
        assert active_user.joined_group.is_active is False
        assert active_user.joined_group.register_step_1_completed is True
        assert active_user.joined_group.register_step_2_completed is True
        assert active_user.joined_group.register_step_3_completed is True
        assert active_user.joined_group.register_step_4_completed is True
        assert active_user.joined_group.register_step_all_confirmed is False

        updated_group = Group.objects.get(id=active_user.joined_group.id)
        assert updated_group.title == "test_title"
        assert updated_group.introduction == "test_introduction"
        assert updated_group.desired_other_group_member_number == 3
        assert orig_title != updated_group.title
        assert orig_introduction != updated_group.introduction
        assert (
            orig_desired_other_group_member_number
            != updated_group.desired_other_group_member_number
        )
        assert (
            orig_desired_other_group_member_avg_age_range
            != updated_group.desired_other_group_member_avg_age_range
        )

    def test_registration_step_4_if_unauthenticated(self, api_client):
        # Do step 4
        res = api_client.patch(
            self.STEP_4_ENDPOINT,
            data={
                "title": "test_title",
                "introduction": "test_introduction",
                "desired_other_group_member_number": 3,
                "desired_other_group_member_avg_age_range": [20, 28],
            },
        )
        assert res.status_code == 401

    def test_registration_step_4_if_not_group_leader(self, api_client):
        active_user = ActiveUserFactory(joined_group=None)
        api_client.force_authenticate(user=active_user)

        # Do step 4
        res = api_client.patch(
            self.STEP_4_ENDPOINT,
            data={
                "title": "test_title",
                "introduction": "test_introduction",
                "desired_other_group_member_number": 3,
                "desired_other_group_member_avg_age_range": [20, 28],
            },
        )
        assert res.status_code == 403
        assert active_user.joined_group is None

    def test_registration_step_4_if_not_completed_step_1(self, api_client):
        active_user = ActiveUserFactory(joined_group=None)
        api_client.force_authenticate(user=active_user)

        # Do step 4
        res = api_client.patch(
            self.STEP_4_ENDPOINT,
            data={
                "title": "test_title",
                "introduction": "test_introduction",
                "desired_other_group_member_number": 3,
                "desired_other_group_member_avg_age_range": [20, 28],
            },
        )
        assert res.status_code == 403
        assert active_user.joined_group is None

    def test_registration_step_4_if_not_completed_step_2(self, hotplaces, api_client):
        active_user = ActiveUserFactory(joined_group=None)
        api_client.force_authenticate(user=active_user)

        # Do step 1
        geoinfo = generate_rand_geoopt_within_boundary(
            RANDOM_HOTPLACE_INFO[RANDOM_HOTPLACE_NAMES[0]]["zone_boundary_geoinfos"]
        )
        res = api_client.post(
            self.STEP_1_ENDPOINT,
            data={"gps_geoinfo": geoinfo},
        )
        assert res.status_code == 201

        # Do step 4
        res = api_client.patch(
            self.STEP_4_ENDPOINT,
            data={
                "title": "test_title",
                "introduction": "test_introduction",
                "desired_other_group_member_number": 3,
                "desired_other_group_member_avg_age_range": [20, 28],
            },
        )
        assert res.status_code == 403
        assert active_user.joined_group is not None
        assert active_user.joined_group.is_active is False
        assert active_user.joined_group.desired_other_group_member_number is None
        assert active_user.joined_group.desired_other_group_member_avg_age_range is None
        assert active_user.joined_group.register_step_1_completed is True
        assert active_user.joined_group.register_step_2_completed is False
        assert active_user.joined_group.register_step_3_completed is False
        assert active_user.joined_group.register_step_4_completed is False
        assert active_user.joined_group.register_step_all_confirmed is False

    def test_registration_step_4_if_not_completed_step_3(self, hotplaces, api_client):
        active_user = ActiveUserFactory(joined_group=None)
        api_client.force_authenticate(user=active_user)

        # Do step 1
        geoinfo = generate_rand_geoopt_within_boundary(
            RANDOM_HOTPLACE_INFO[RANDOM_HOTPLACE_NAMES[0]]["zone_boundary_geoinfos"]
        )
        res = api_client.post(
            self.STEP_1_ENDPOINT,
            data={"gps_geoinfo": geoinfo},
        )
        assert res.status_code == 201

        # Do step 2
        friends = ActiveUserFactory.create_batch(size=3, joined_group=None)
        friends_codes = []
        for friend in friends:
            api_client.force_authenticate(user=friend)
            res = api_client.post(self.INVITATION_ENDPOINT)
            assert res.status_code == 201
            friends_codes.append(res.data["code"])

        api_client.force_authenticate(user=active_user)
        res = api_client.post(
            self.STEP_2_ENDPOINT,
            data={"invitation_codes": friends_codes},
        )
        assert res.status_code == 200

        # Do step 4
        res = api_client.patch(
            self.STEP_4_ENDPOINT,
            data={
                "title": "test_title",
                "introduction": "test_introduction",
                "desired_other_group_member_number": 3,
                "desired_other_group_member_avg_age_range": [20, 28],
            },
        )
        assert res.status_code == 403
        assert active_user.joined_group is not None
        assert active_user.joined_group.is_active is False
        assert active_user.joined_group.desired_other_group_member_number is None
        assert active_user.joined_group.desired_other_group_member_avg_age_range is None
        assert active_user.joined_group.register_step_1_completed is True
        assert active_user.joined_group.register_step_2_completed is True
        assert active_user.joined_group.register_step_3_completed is False
        assert active_user.joined_group.register_step_4_completed is False
        assert active_user.joined_group.register_step_all_confirmed is False

    # ------------------
    #  Step Confirmation
    # ------------------

    def test_registration_step_confirm_all_good(self, hotplaces, api_client):
        active_user = ActiveUserFactory(joined_group=None)
        api_client.force_authenticate(user=active_user)

        # Do Step 1
        geoinfo = generate_rand_geoopt_within_boundary(
            RANDOM_HOTPLACE_INFO[RANDOM_HOTPLACE_NAMES[0]]["zone_boundary_geoinfos"]
        )
        res = api_client.post(
            self.STEP_1_ENDPOINT,
            data={"gps_geoinfo": geoinfo},
        )
        assert res.status_code == 201

        # Do step 2
        friends = ActiveUserFactory.create_batch(size=3, joined_group=None)
        friends_codes = []
        for friend in friends:
            api_client.force_authenticate(user=friend)
            res = api_client.post(self.INVITATION_ENDPOINT)
            assert res.status_code == 201
            friends_codes.append(res.data["code"])

        api_client.force_authenticate(user=active_user)
        res = api_client.post(
            self.STEP_2_ENDPOINT,
            data={"invitation_codes": friends_codes},
        )
        assert res.status_code == 200

        # Do Step 3
        image = Image.new("RGBA", size=(50, 50), color=(155, 0, 0))
        file = tempfile.NamedTemporaryFile(suffix=".png")
        image.save(file)

        with open(file.name, "rb") as data:
            res = api_client.post(
                self.STEP_3_ENDPOINT,
                data={"image": data},
                format="multipart",
            )
            assert res.status_code == 200

        # Do Step 4
        res = api_client.patch(
            self.STEP_4_ENDPOINT,
            data={
                "title": "test_title",
                "introduction": "test_introduction",
                "desired_other_group_member_number": 3,
                "desired_other_group_member_avg_age_range": [20, 28],
            },
        )
        assert res.status_code == 200

        # Do Step Confirmation
        res = api_client.post(self.STEP_CONFIRM_ENDPOINT)
        assert res.status_code == 200
        assert active_user.joined_group is not None
        assert active_user.joined_group.is_active is True
        assert active_user.joined_group.register_step_1_completed is True
        assert active_user.joined_group.register_step_2_completed is True
        assert active_user.joined_group.register_step_3_completed is True
        assert active_user.joined_group.register_step_4_completed is True
        assert active_user.joined_group.register_step_all_confirmed is True

    def test_registration_step_confirm_if_unauthenticated(self, api_client):
        # Do step confirm
        res = api_client.post(self.STEP_CONFIRM_ENDPOINT)
        assert res.status_code == 401

    def test_registration_step_confirm_if_not_group_leader(self, api_client):
        active_user = ActiveUserFactory(joined_group=None)
        api_client.force_authenticate(user=active_user)

        # Do step confirm
        res = api_client.post(self.STEP_CONFIRM_ENDPOINT)
        assert res.status_code == 403
        assert active_user.joined_group is None

    def test_registration_step_confirm_if_not_completed_step_1(self, api_client):
        active_user = ActiveUserFactory(joined_group=None)
        api_client.force_authenticate(user=active_user)

        # Do step confirm
        res = api_client.post(self.STEP_CONFIRM_ENDPOINT)
        assert res.status_code == 403
        assert active_user.joined_group is None

    def test_registration_step_confirm_if_not_completed_step_2(
        self, hotplaces, api_client
    ):
        active_user = ActiveUserFactory(joined_group=None)
        api_client.force_authenticate(user=active_user)

        # Do step 1
        geoinfo = generate_rand_geoopt_within_boundary(
            RANDOM_HOTPLACE_INFO[RANDOM_HOTPLACE_NAMES[0]]["zone_boundary_geoinfos"]
        )
        res = api_client.post(
            self.STEP_1_ENDPOINT,
            data={"gps_geoinfo": geoinfo},
        )
        assert res.status_code == 201

        # Do step confirm
        res = api_client.post(self.STEP_CONFIRM_ENDPOINT)
        assert res.status_code == 403
        assert active_user.joined_group is not None
        assert active_user.joined_group.is_active is False
        assert active_user.joined_group.desired_other_group_member_number is None
        assert active_user.joined_group.desired_other_group_member_avg_age_range is None
        assert active_user.joined_group.register_step_1_completed is True
        assert active_user.joined_group.register_step_2_completed is False
        assert active_user.joined_group.register_step_3_completed is False
        assert active_user.joined_group.register_step_4_completed is False
        assert active_user.joined_group.register_step_all_confirmed is False

    def test_registration_step_confirm_if_not_completed_step_3(
        self, hotplaces, api_client
    ):
        active_user = ActiveUserFactory(joined_group=None)
        api_client.force_authenticate(user=active_user)

        # Do step 1
        geoinfo = generate_rand_geoopt_within_boundary(
            RANDOM_HOTPLACE_INFO[RANDOM_HOTPLACE_NAMES[0]]["zone_boundary_geoinfos"]
        )
        res = api_client.post(
            self.STEP_1_ENDPOINT,
            data={"gps_geoinfo": geoinfo},
        )
        assert res.status_code == 201

        # Do step 2
        friends = ActiveUserFactory.create_batch(size=3, joined_group=None)
        friends_codes = []
        for friend in friends:
            api_client.force_authenticate(user=friend)
            res = api_client.post(self.INVITATION_ENDPOINT)
            assert res.status_code == 201
            friends_codes.append(res.data["code"])

        api_client.force_authenticate(user=active_user)
        res = api_client.post(
            self.STEP_2_ENDPOINT,
            data={"invitation_codes": friends_codes},
        )
        assert res.status_code == 200

        # Do step confirm
        res = api_client.post(self.STEP_CONFIRM_ENDPOINT)
        assert res.status_code == 403
        assert active_user.joined_group is not None
        assert active_user.joined_group.is_active is False
        assert active_user.joined_group.desired_other_group_member_number is None
        assert active_user.joined_group.desired_other_group_member_avg_age_range is None
        assert active_user.joined_group.register_step_1_completed is True
        assert active_user.joined_group.register_step_2_completed is True
        assert active_user.joined_group.register_step_3_completed is False
        assert active_user.joined_group.register_step_4_completed is False
        assert active_user.joined_group.register_step_all_confirmed is False

    def test_registration_step_confirm_if_not_completed_step_4(
        self, hotplaces, api_client
    ):
        active_user = ActiveUserFactory(joined_group=None)
        api_client.force_authenticate(user=active_user)

        # Do step 1
        geoinfo = generate_rand_geoopt_within_boundary(
            RANDOM_HOTPLACE_INFO[RANDOM_HOTPLACE_NAMES[0]]["zone_boundary_geoinfos"]
        )
        res = api_client.post(
            self.STEP_1_ENDPOINT,
            data={"gps_geoinfo": geoinfo},
        )
        assert res.status_code == 201

        # Do step 2
        friends = ActiveUserFactory.create_batch(size=3, joined_group=None)
        friends_codes = []
        for friend in friends:
            api_client.force_authenticate(user=friend)
            res = api_client.post(self.INVITATION_ENDPOINT)
            assert res.status_code == 201
            friends_codes.append(res.data["code"])

        api_client.force_authenticate(user=active_user)
        res = api_client.post(
            self.STEP_2_ENDPOINT,
            data={"invitation_codes": friends_codes},
        )
        assert res.status_code == 200

        # Do Step 3
        image = Image.new("RGBA", size=(50, 50), color=(155, 0, 0))
        file = tempfile.NamedTemporaryFile(suffix=".png")
        image.save(file)

        with open(file.name, "rb") as data:
            res = api_client.post(
                self.STEP_3_ENDPOINT,
                data={"image": data},
                format="multipart",
            )
            assert res.status_code == 200

        # Do step confirm
        res = api_client.post(self.STEP_CONFIRM_ENDPOINT)
        assert res.status_code == 403
        assert active_user.joined_group is not None
        assert active_user.joined_group.is_active is False
        assert active_user.joined_group.desired_other_group_member_number is None
        assert active_user.joined_group.desired_other_group_member_avg_age_range is None
        assert active_user.joined_group.register_step_1_completed is True
        assert active_user.joined_group.register_step_2_completed is True
        assert active_user.joined_group.register_step_3_completed is True
        assert active_user.joined_group.register_step_4_completed is False
        assert active_user.joined_group.register_step_all_confirmed is False

    # -----------
    #  Unregister
    # -----------
    def test_registration_step_unregister_all_good(self, hotplaces, api_client):
        active_user = ActiveUserFactory(joined_group=None)
        api_client.force_authenticate(user=active_user)

        # Do Step 1
        geoinfo = generate_rand_geoopt_within_boundary(
            RANDOM_HOTPLACE_INFO[RANDOM_HOTPLACE_NAMES[0]]["zone_boundary_geoinfos"]
        )
        res = api_client.post(
            self.STEP_1_ENDPOINT,
            data={"gps_geoinfo": geoinfo},
        )
        assert res.status_code == 201

        # Do step 2
        friends = ActiveUserFactory.create_batch(size=3, joined_group=None)
        friends_codes = []
        for friend in friends:
            api_client.force_authenticate(user=friend)
            res = api_client.post(self.INVITATION_ENDPOINT)
            assert res.status_code == 201
            friends_codes.append(res.data["code"])

        api_client.force_authenticate(user=active_user)
        res = api_client.post(
            self.STEP_2_ENDPOINT,
            data={"invitation_codes": friends_codes},
        )
        assert res.status_code == 200

        # Do Step 3
        image = Image.new("RGBA", size=(50, 50), color=(155, 0, 0))
        file = tempfile.NamedTemporaryFile(suffix=".png")
        image.save(file)

        with open(file.name, "rb") as data:
            res = api_client.post(
                self.STEP_3_ENDPOINT,
                data={"image": data},
                format="multipart",
            )
            assert res.status_code == 200

        # Do Step 4
        res = api_client.patch(
            self.STEP_4_ENDPOINT,
            data={
                "title": "test_title",
                "introduction": "test_introduction",
                "desired_other_group_member_number": 3,
                "desired_other_group_member_avg_age_range": [20, 28],
            },
        )
        assert res.status_code == 200

        # Do Step Confirmation
        res = api_client.post(self.STEP_CONFIRM_ENDPOINT)
        assert res.status_code == 200

        orig_group = Group.objects.get(id=active_user.joined_group.id)
        assert orig_group.is_active is True

        # Unregister
        res = api_client.post(self.UNREGISTER_ENDPOINT)
        orig_group = Group.objects.get(id=orig_group.id)
        active_user = User.objects.get(id=active_user.id)
        assert res.status_code == 200
        assert orig_group.is_active is False
        assert active_user.joined_group is None
        assert active_user.is_group_leader is False
        for friend in friends:
            assert friend.joined_group is None

    def test_registration_step_unregister_if_unauthenticated(self, api_client):
        # Do step unregister
        res = api_client.post(self.UNREGISTER_ENDPOINT)
        assert res.status_code == 401

    def test_registration_step_unregister_if_not_group_leader(self, api_client):
        active_user = ActiveUserFactory(joined_group=None)
        api_client.force_authenticate(user=active_user)

        # Do step unregister
        res = api_client.post(self.UNREGISTER_ENDPOINT)
        assert res.status_code == 403
        assert active_user.joined_group is None


class TestGroupInvitationCodeEndpoints:
    INVITATION_ENDPOINT = "/api/group/invitation-code/generate/"

    # ----------------------
    #  Invitation Code Flow
    # ----------------------
    def test_invitation_code_generation(self, api_client):
        friend = ActiveUserFactory.create(joined_group=None)
        api_client.force_authenticate(user=friend)
        res = api_client.post(self.INVITATION_ENDPOINT)
        assert res.status_code == 201
