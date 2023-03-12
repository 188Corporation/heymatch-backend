from dj_rest_auth.views import LoginView, LogoutView
from django.urls import path

from .api.views import EmailVerificationViewSet, PhoneRegistrationViewSet

app_name = "auth"

phone_code_generate_view = PhoneRegistrationViewSet.as_view({"post": "register"})
email_code_generate_view = EmailVerificationViewSet.as_view({"post": "get_code"})
email_code_authorize_view = EmailVerificationViewSet.as_view({"post": "authorize"})
# stream_token_generate_view = StreamTokenViewSet.as_view({"get": "retrieve"})

urlpatterns = [
    # dj-rest-auth
    path(
        "phone/get-code/",
        phone_code_generate_view,
        name="phone-verification-code-generate",
    ),
    path(
        "phone/authorize/",
        LoginView.as_view(),
        name="phone-verification-code-authorize",
    ),
    path(
        "email/get-code/",
        email_code_generate_view,
        name="email-verification-code-generate",
    ),
    path(
        "email/authorize/",
        email_code_authorize_view,
        name="email-verification-code-authorize",
    ),
    path("logout/", LogoutView.as_view(), name="rest_logout"),
    # path(
    #     "stream/token/", stream_token_generate_view, name="stream-user-token-generate"
    # ),
]
