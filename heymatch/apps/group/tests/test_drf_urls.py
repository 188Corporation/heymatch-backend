import pytest
from django.urls import resolve, reverse

pytestmark = pytest.mark.django_db


@pytest.mark.skip
def test_group_registration_step_1():
    assert (
        reverse("api:group:group-registration-step-1")
        == "/api/groups/registration/step/1/"
    )
    assert (
        resolve("/api/groups/registration/step/1/").view_name
        == "api:group:group-registration-step-1"
    )


@pytest.mark.skip
def test_group_registration_step_2():
    assert (
        reverse("api:group:group-registration-step-2")
        == "/api/groups/registration/step/2/"
    )
    assert (
        resolve("/api/groups/registration/step/2/").view_name
        == "api:group:group-registration-step-2"
    )


@pytest.mark.skip
def test_group_registration_step_3():
    assert (
        reverse("api:group:group-registration-step-3")
        == "/api/groups/registration/step/3/"
    )
    assert (
        resolve("/api/groups/registration/step/3/").view_name
        == "api:group:group-registration-step-3"
    )


@pytest.mark.skip
def test_group_registration_step_4():
    assert (
        reverse("api:group:group-registration-step-4")
        == "/api/groups/registration/step/4/"
    )
    assert (
        resolve("/api/groups/registration/step/4/").view_name
        == "api:group:group-registration-step-4"
    )


@pytest.mark.skip
def test_group_registration_step_confirm():
    assert (
        reverse("api:group:group-registration-step-confirm")
        == "/api/groups/registration/step/confirm/"
    )
    assert (
        resolve("/api/groups/registration/step/confirm/").view_name
        == "api:group:group-registration-step-confirm"
    )


@pytest.mark.skip
def test_group_registration_unregister():
    assert (
        reverse("api:group:group-registration-unregister")
        == "/api/groups/registration/unregister/"
    )
    assert (
        resolve("/api/groups/registration/unregister/").view_name
        == "api:group:group-registration-unregister"
    )


#
# def test_group_invitation_code_generate():
#     assert (
#         reverse("api:group:group-invitation-code-generate")
#         == "/api/groups/invitation-code/generate/"
#     )
#     assert (
#         resolve("/api/groups/invitation-code/generate/").view_name
#         == "api:group:group-invitation-code-generate"
#     )
