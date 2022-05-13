from django.urls import path

from heythere.apps.group.api.views import (
    GroupInvitationCodeViewSet,
    GroupRegisterConfirmationViewSet,
    GroupRegisterStatusViewSet,
    GroupRegisterStep1ViewSet,
    GroupRegisterStep2ViewSet,
    GroupRegisterStep3ViewSet,
    GroupRegisterStep4ViewSet,
    GroupUnregisterViewSet,
)

app_name = "group"

group_register_status = GroupRegisterStatusViewSet.as_view({"get": "retrieve"})
group_register_step_1_view = GroupRegisterStep1ViewSet.as_view({"post": "create"})
group_register_step_2_view = GroupRegisterStep2ViewSet.as_view({"post": "invite"})
group_register_step_3_view = GroupRegisterStep3ViewSet.as_view({"put": "update"})
group_register_step_4_view = GroupRegisterStep4ViewSet.as_view({"put": "update"})
group_register_step_confirm_view = GroupRegisterConfirmationViewSet.as_view(
    {"put": "update"}
)
group_register_unregister_view = GroupUnregisterViewSet.as_view({"post": "unregister"})
group_invite_code_generate_view = GroupInvitationCodeViewSet.as_view(
    {
        "post": "create",
    }
)

urlpatterns = [
    # Group Registration
    path(
        "registration/status/",
        group_register_status,
        name="group-registration-status",
    ),
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
