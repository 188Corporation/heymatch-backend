from django.urls import path

from heythere.apps.users.api.views import UserDetailViewSet

app_name = "users"

user_detail = UserDetailViewSet.as_view()

urlpatterns = [
    path("detail/", user_detail, name="user-detail"),
]
