from django.urls import path

from heythere.apps.group.api.views import (
    GroupRegisterStep1ViewSet,
    GroupRegisterStep2ViewSet,
    GroupRegisterStep3ViewSet,
    GroupRegisterStep4ViewSet,
    GroupRegisterStep5ViewSet,
)

app_name = "group"

group_register_step_1_view = GroupRegisterStep1ViewSet.as_view(
    {"get": "retrieve", "post": "create"}
)
group_register_step_2_view = GroupRegisterStep2ViewSet.as_view(
    {"get": "retrieve", "post": "create", "put": "update"}
)
group_register_step_3_view = GroupRegisterStep3ViewSet.as_view(
    {"get": "retrieve", "post": "create", "put": "update"}
)
group_register_step_4_view = GroupRegisterStep4ViewSet.as_view(
    {"get": "retrieve", "post": "create"}
)

group_register_step_5_view = GroupRegisterStep5ViewSet.as_view(
    {"get": "retrieve", "post": "create"}
)

urlpatterns = [
    # Group Registration
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
        "registration/step/5/",
        group_register_step_5_view,
        name="group-registration-step-5",
    ),
]
