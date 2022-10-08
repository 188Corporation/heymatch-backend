from django.urls import path

from heymatch.apps.group.api.views import (
    GroupDetailViewSet,
    GroupInvitationCodeViewSet,
    GroupRegisterConfirmationViewSet,
    GroupRegisterStep1ViewSet,
    GroupRegisterStep2ViewSet,
    GroupRegisterStep3ViewSet,
    GroupRegisterStep4ViewSet,
    GroupsGenericViewSet,
    GroupUnregisterViewSet,
)

app_name = "group"

group_generic_view = GroupsGenericViewSet.as_view({"get": "list", "post": "create"})
group_detail_view = GroupDetailViewSet.as_view({"get": "retrieve"})
group_registration_view = GroupUnregisterViewSet.as_view({"post": "register"})
group_register_step_1_view = GroupRegisterStep1ViewSet.as_view({"post": "validate_gps"})
group_register_step_2_view = GroupRegisterStep2ViewSet.as_view(
    {"post": "invite_member"}
)
group_register_step_3_view = GroupRegisterStep3ViewSet.as_view(
    {
        "post": "upload_photo",
        "patch": "update_photo",
    }
)
group_register_step_4_view = GroupRegisterStep4ViewSet.as_view(
    {"patch": "write_profile"}
)
group_register_step_confirm_view = GroupRegisterConfirmationViewSet.as_view(
    {"post": "confirm"}
)
group_register_unregister_view = GroupUnregisterViewSet.as_view({"post": "unregister"})
group_invite_code_generate_view = GroupInvitationCodeViewSet.as_view(
    {
        "post": "create",
    }
)

urlpatterns = [
    path("", group_generic_view, name="group-generic"),
    path("<int:group_id>/", group_detail_view, name="group-detail"),
    path(
        "registration/step/1/",
        group_register_step_1_view,
        name="group-registration-step-1",
    ),
    path(
        "registration/step/2/",
        group_register_step_2_view,
        name="group-registration-step-2",
    ),
    path(
        "registration/step/3/",
        group_register_step_3_view,
        name="group-registration-step-3",
    ),
    path(
        "registration/step/4/",
        group_register_step_4_view,
        name="group-registration-step-4",
    ),
    path(
        "registration/step/confirm/",
        group_register_step_confirm_view,
        name="group-registration-step-confirm",
    ),
    # Group Un-register
    path(
        "registration/unregister/",
        group_register_unregister_view,
        name="group-registration-unregister",
    ),
    # Group Invitation
    path(
        "invitation-code/generate/",
        group_invite_code_generate_view,
        name="group-invitation-code-generate",
    ),
]
