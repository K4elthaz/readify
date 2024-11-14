from django.urls import path

from app.authentication.views.services import (
    signup_service,
    select_role_service,
    select_preferences_service,
    follow_author_service,
    signin_service,
    logout_service,
    unfollow_service,
    referral_code_service,
    update_user_profile,
    change_password,
    forgot_password_service,
    reset_password_service,
)
from app.authentication.views.views import (
    SignInView,
    SignUpView,
    SelectRoleView,
    SelectPreferencesView,
    DoneOnboardingView,
    FollowAuthorsView,
    UserProfileView,
    ReferralCodeView,
    verify_email,
    auth_receiver,
    AgreementView,
    ForgotPasswordView,
    ResetPasswordView,
    TermsAndConditionView,
)

service_urlpatterns = [
    path("signup/service", signup_service, name="signup_service"),
    path(
        "select-role/<str:id>/<str:role>",
        select_role_service,
        name="select_role_service",
    ),
    path(
        "select-preferences/<str:id>",
        select_preferences_service,
        name="select_preferences_service",
    ),
    path(
        "follow/author/<str:id>/<str:author_id>",
        follow_author_service,
        name="follow_author_service",
    ),
    path(
        "signin/service",
        signin_service,
        name="signin_service",
    ),
    path(
        "signout",
        logout_service,
        name="logout_service",
    ),
    path(
        "unfollow/<str:id>",
        unfollow_service,
        name="unfollow_service",
    ),
    path(
        "referral-code/username/<str:id>",
        referral_code_service,
        name="referral_code_service",
    ),
    path(
        "profile/update/",
        update_user_profile,
        name="update_user_profile",
    ),
    path(
        "profile/password/update/",
        change_password,
        name="change_password",
    ),
    path(
        "password/forgot/",
        forgot_password_service,
        name="forgot_password_service",
    ),
    path(
        "password/reset/<str:encrypted_email>/",
        reset_password_service,
        name="reset_password_service",
    ),
]


urlpatterns = [
    path("signin/", SignInView.as_view(), name="signin"),
    path("auth-receiver", auth_receiver, name="auth_receiver"),
    path("signup/", SignUpView.as_view(), name="signup"),
    path("select/role/<str:id>", SelectRoleView.as_view(), name="select_role"),
    path(
        "select/preferences/<str:id>",
        SelectPreferencesView.as_view(),
        name="select_role",
    ),
    path(
        "authors/follow/<str:id>",
        FollowAuthorsView.as_view(),
        name="follow-authors",
    ),
    path(
        "onboarding/done/<str:id>",
        DoneOnboardingView.as_view(),
        name="done_onboarding",
    ),
    path(
        "profile/<str:pk>",
        UserProfileView.as_view(),
        name="user_profile",
    ),
    path(
        "referral-code/<str:pk>",
        ReferralCodeView.as_view(),
        name="referral_code",
    ),
    path(
        "agreement/<str:id>",
        AgreementView.as_view(),
        name="agreement",
    ),
    path(
        "verify-email/<str:email_bytes>",
        verify_email,
        name="verify_email",
    ),
    path(
        "forgot-password/",
        ForgotPasswordView.as_view(),
        name="forgot_password",
    ),
    path(
        "reset-password/<str:encrypted_email>/",
        ResetPasswordView.as_view(),
        name="reset_password",
    ),
    path(
        "terms-and-conditions",
        TermsAndConditionView.as_view(),
        name="terms_and_conditions",
    ),
] + service_urlpatterns
