import pytest
from django.shortcuts import reverse
from rest_framework.test import APIClient

from heymatch.apps.user.tests.factories import ActiveUserFactory

pytestmark = pytest.mark.django_db


@pytest.mark.skip
class TestUserWithGroupFullInfoEndpoints:
    ENDPOINT = "/api/users/my/"

    def test_registration_status_all_good(self, api_client: APIClient):
        active_user = ActiveUserFactory(joined_group=None)
        api_client.force_authenticate(user=active_user)
        res = api_client.get(self.ENDPOINT)
        assert res.status_code == 200

    def test_registration_status_if_not_authenticated(self, api_client: APIClient):
        res = api_client.get(self.ENDPOINT)
        assert res.status_code == 401


class TestPhoneVerificationEndpoints:
    def test_phone_verification_flow(self, mocker):
        active_user = ActiveUserFactory(phone_number="+821032433994")

        mocker.patch("phone_verify.services.PhoneVerificationService.send_verification")

        # phone register
        url = reverse("api:auth:phone-verification-code-generate")
        client = APIClient()
        res = client.post(url, data={"phone_number": active_user.phone_number})
        assert res.status_code == 200

        # phone authorize (performs login or registration at the same time)
        # url = reverse("api:auth:phone-verification-code-authorize")
        # session_token = res.data["session_token"]
        # security_code = SMSVerification.objects.get(
        #     phone_number=active_user.phone_number
        # ).security_code
        # res = client.post(
        #     url,
        #     data={
        #         "phone_number": active_user.phone_number,
        #         "session_token": session_token,
        #         "security_code": security_code,
        #     },
        # )
        # assert res.status_code == 200
