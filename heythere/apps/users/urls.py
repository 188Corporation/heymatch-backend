from django.urls import path

from heythere.apps.users.api.views import UserProfileViewSet

app_name = "users"

user_detail = UserProfileViewSet.as_view()

urlpatterns = [
    path("profile/", user_detail, name="user-profile-detail"),
]
