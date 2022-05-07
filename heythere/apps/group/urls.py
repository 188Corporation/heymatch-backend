from django.urls import path

from heythere.apps.group.api.views import GroupRegistrationStepViewSet

app_name = "group"

group_register_step_detail = GroupRegistrationStepViewSet.as_view({"get": "retrieve"})
group_register_step_register = GroupRegistrationStepViewSet.as_view({"post": "create"})

urlpatterns = [
    # Group Registration
    path(
        "group/registration/step/<int:step_num>/",
        group_register_step_detail,
        name="group-registration-step-detail",
    ),
    path(
        "group/registration/step/<int:step_num>/",
        group_register_step_register,
        name="group-registration-step-register",
    ),
]
