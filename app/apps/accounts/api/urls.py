from django.urls import path

from apps.accounts.api.views import (
    # company resource views
    CreateCompanyAndUserAccountAPIView,
    CompanyInvitationAPIView,
    CompanyRetrieveUpdateDestroyAPIView,
    CompanyMembershipPermissionsListAPIView,

    # user resource views
    UserInvitationTokenBasedRegistrationAPIView,
    ForgotPasswordAPIView,
    ResetPasswordAPIView,
    UserListAPIView,
    UserRetrieveDestroyAPIView,
    UsersCompanyMembershipPermissionsUpdateAPIView,

    # login views
    LoginAPIView,
    RefreshTokenAPIView,

    # "me" resource views
    ConfirmEmailAddressAPIView,
    UpdatePasswordAPIView,
    UserProfilePhotoUploadDeleteAPIView,
    UserProfileRetrieveUpdateAPIView,
    MeUpdateDestroyAPIView,

    # utility resource views
    CheckEmailIsInUseAPIView,
    CheckCompanyNameIsInUseAPIView,
    CheckPasswordResetTokenIsValidAPIView,
    CheckCompanyInvitationTokenIsValidAPIView
)


company_related_resources = [
    path(
        'company/registration/',
        CreateCompanyAndUserAccountAPIView.as_view(),
        name='create_company_and_user_account'
    ),
    path(
        'company/invitation/',
        CompanyInvitationAPIView.as_view(),
        name='company_invitation'
    ),
    path(
        'company/',
        CompanyRetrieveUpdateDestroyAPIView.as_view(),
        name='company_retrieve_update_destroy'
    ),
    path(
        'company/membership-permissions/',
        CompanyMembershipPermissionsListAPIView.as_view(),
        name='company_membership_permissions_list',
    ),
]

user_related_resources = [
    path(
        'users/registration/<str:invitation_token>/',
        UserInvitationTokenBasedRegistrationAPIView.as_view(),
        name='user_invitation_token_based_registration',
    ),
    path(
        'users/forgot-password/',
        ForgotPasswordAPIView.as_view(),
        name='user_forgot_password',
    ),
    path(
        'users/reset-password/<str:password_reset_token>/',
        ResetPasswordAPIView.as_view(),
        name='user_reset_password',
    ),
    path(
        'users/',
        UserListAPIView.as_view(),
        name='user_list'
    ),
    path(
        'users/<int:pk>/',
        UserRetrieveDestroyAPIView.as_view(),
        name='user_retrieve_destroy'
    ),
    path(
        'users/<int:pk>/update-company-membership-permissions/',
        UsersCompanyMembershipPermissionsUpdateAPIView.as_view(),
        name='update_user_company_membership_permissions'
    ),
]

login_related_resources = [
    path(
        'login/',
        LoginAPIView.as_view(),
        name='login'
    ),
    path(
        'access-token-refresh/',
        RefreshTokenAPIView.as_view(),
        name='auth_token_refresh'
    ),
]

me_ralated_resources = [
    path(
        'me/email-address-confirmation/<str:email_confirmation_token>/',
        ConfirmEmailAddressAPIView.as_view(),
        name='me_email_address_confirmation',
    ),
    path(
        'me/update-password/',
        UpdatePasswordAPIView.as_view(),
        name='me_update_password',
    ),
    path(
        'me/profile-photo/',
        UserProfilePhotoUploadDeleteAPIView.as_view(),
        name='me_profile_photo_upload_delete',
    ),
    path(
        'me/profile/',
        UserProfileRetrieveUpdateAPIView.as_view(),
        name='me_profile_retrieve_update'
    ),
    path(
        'me/',
        MeUpdateDestroyAPIView.as_view(),
        name='me_update_destroy'
    ),
]

utility_related_resources = [
    path(
        'utility/email-in-use/',
        CheckEmailIsInUseAPIView.as_view(),
        name='utility_email_is_in_use',
    ),
    path(
        'utility/company-name-in-use/',
        CheckCompanyNameIsInUseAPIView.as_view(),
        name='utility_company_name_is_in_use',
    ),
    path(
        'utility/password-reset-token-valid/<str:password_reset_token>/',
        CheckPasswordResetTokenIsValidAPIView.as_view(),
        name='utility_password_reset_token_is_valid',
    ),
    path(
        'utility/company-invitation-token-valid/<str:company_invitation_token>/',
        CheckCompanyInvitationTokenIsValidAPIView.as_view(),
        name='utility_company_invitation_token_is_valid',
    )
]

urlpatterns = [
    *company_related_resources,
    *user_related_resources,
    *login_related_resources,
    *me_ralated_resources,
    *utility_related_resources,
]