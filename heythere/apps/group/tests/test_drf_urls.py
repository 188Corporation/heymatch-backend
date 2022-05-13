import pytest
from django.urls import resolve, reverse

pytestmark = pytest.mark.django_db


def test_group_registration_status():
    assert (
        reverse("api:group:group-registration-status")
        == "/api/group/registration/status/"
    )
    assert (
        resolve("/api/group/registration/status/").view_name
        == "api:group:group-registration-status"
    )


def test_group_registration_step_1():
    assert (
        reverse("api:group:group-registration-step-1")
        == "/api/group/registration/step/1/"
    )
    assert (
        resolve("/api/group/registration/step/1/").view_name
        == "api:group:group-registration-step-1"
    )


def test_group_registration_step_2():
    assert (
        reverse("api:group:group-registration-step-2")
        == "/api/group/registration/step/2/"
    )
    assert (
        resolve("/api/group/registration/step/2/").view_name
        == "api:group:group-registration-step-2"
    )


def test_group_registration_step_3():
    assert (
        reverse("api:group:group-registration-step-3")
        == "/api/group/registration/step/3/"
    )
    assert (
        resolve("/api/group/registration/step/3/").view_name
        == "api:group:group-registration-step-3"
    )


def test_group_registration_step_4():
    assert (
        reverse("api:group:group-registration-step-4")
        == "/api/group/registration/step/4/"
    )
    assert (
        resolve("/api/group/registration/step/4/").view_name
        == "api:group:group-registration-step-4"
    )


def test_group_registration_step_confirm():
    assert (
        reverse("api:group:group-registration-step-confirm")
        == "/api/group/registration/step/confirm/"
    )
    assert (
        resolve("/api/group/registration/step/confirm/").view_name
        == "api:group:group-registration-step-confirm"
    )


def test_group_registration_unregister():
    assert (
        reverse("api:group:group-registration-unregister")
        == "/api/group/registration/unregister/"
    )
    assert (
        resolve("/api/group/registration/unregister/").view_name
        == "api:group:group-registration-unregister"
    )


def test_group_invitation_code_generate():
    assert (
        reverse("api:group:group-invitation-code-generate")
        == "/api/group/invitation-code/generate/"
    )
    assert (
        resolve("/api/group/invitation-code/generate/").view_name
        == "api:group:group-invitation-code-generate"
    )
