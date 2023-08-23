from django.urls import path

from .api.views import (
    TempUserCreateViewSet,
    UserInvitationCodeViewSet,
    UsernameUniquenessCheckViewSet,
    UserOnboardingViewSet,
    UsersAdmobSSVViewSet,
    UserWithGroupFullInfoViewSet,
    UserWithGroupProfilePhotoViewSet,
)

app_name = "user"

users_my_view = UserWithGroupFullInfoViewSet.as_view(
    {
        "get": "retrieve",
        "put": "update",
        "delete": "schedule_delete",
    }
)
users_my_profile_photo_view = UserWithGroupProfilePhotoViewSet.as_view(
    {
        "delete": "delete_profile_photo",
    }
)
users_my_onboarding_view = UserOnboardingViewSet.as_view({"get": "retrieve"})
users_my_onboarding_in_progress_extra_info_view = UserOnboardingViewSet.as_view(
    {"post": "in_progress_extra_info"}
)
users_my_onboarding_complete_extra_info_view = UserOnboardingViewSet.as_view(
    {"post": "complete_extra_info"}
)
users_unique_name_view = UsernameUniquenessCheckViewSet.as_view({"post": "check"})
users_invitation_code_view = UserInvitationCodeViewSet.as_view({"post": "accept"})
users_temp_user_view = TempUserCreateViewSet.as_view({"post": "create"})
users_admob_ssv_view = UsersAdmobSSVViewSet.as_view({"get": "retrieve"})

urlpatterns = [
    path("my/", users_my_view, name="user-my-detail"),
    path(
        "my/profile/photo/",
        users_my_profile_photo_view,
        name="user-my-profile-photo-delete",
    ),
    path(
        "my/onboarding/",
        users_my_onboarding_view,
        name="user-my-onboarding",
    ),
    path(
        "my/onboarding/in-progress/extra-info/",
        users_my_onboarding_in_progress_extra_info_view,
        name="user-my-onboarding-in-progress-extra-info",
    ),
    path(
        "my/onboarding/complete/extra-info/",
        users_my_onboarding_complete_extra_info_view,
        name="user-my-onboarding-complete-extra-info",
    ),
    path("temp-user/", users_temp_user_view, name="temp-user"),
    path("check-username/", users_unique_name_view, name="user-my-check-username"),
    path(
        "invitation/<str:invitation_code>/accept/",
        users_invitation_code_view,
        name="user-my-invitation-accept",
    ),
    # Google Admob SSV
    path("admob-ssv/", users_admob_ssv_view, name="user-admob-ssv"),
]
