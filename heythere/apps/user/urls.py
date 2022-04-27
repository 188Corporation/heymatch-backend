from django.urls import path

from heythere.apps.user.api.views import UserProfileViewSet

app_name = "user"

user_profile_detail = UserProfileViewSet.as_view()

urlpatterns = [
    path("profile/", user_profile_detail, name="user-profile-detail"),
]
