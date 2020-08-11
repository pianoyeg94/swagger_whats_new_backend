from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import serializers
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from shared.exceptions import APIExceptionWithCode200
from apps.accounts.models import CompanyInvitation
from shared.permissions import (
    IsCompanyOwnerOrHasObjectPermissionOrReadOnly,
    HasEmailConfirmed,
    check_object_permissions
)
from apps.accounts.api.serializers import (
    CompanyAccountSerializer,
    ConfirmEmailAddressSerializer,
    CompanyInvitationSerializer,
    UserWithCompanyInvitationSerializer,
    ForgotPasswordSerializer,
    PasswordResetSerializer,
    UserWithTokenSerializer,
    PasswordUpdateSerializer,
    LoginSerializer,
    RefreshTokenSerializer
)

User = get_user_model()


class CreateCompanyAndUserAccountAPIView(generics.CreateAPIView):
    serializer_class = CompanyAccountSerializer


class ConfirmEmailAddressAPIView(generics.UpdateAPIView):
    serializer_class = ConfirmEmailAddressSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_object(self) -> User:
        return self.request.user
    
    def get_serializer_context(self) -> dict:
        context = super().get_serializer_context()
        context['email_confirmation_token'] = self.kwargs.get(
            'email_confirmation_token')
        
        return context


@check_object_permissions(obj=CompanyInvitation, methods=['create'])
class CompanyInvitationAPIView(generics.CreateAPIView):
    serializer_class = CompanyInvitationSerializer
    permission_classes = (
        IsAuthenticated,
        IsCompanyOwnerOrHasObjectPermissionOrReadOnly,
        HasEmailConfirmed
    )
    
    def create(self, request: Request, *args, **kwargs) -> Response:
        """
        Overrides the default "create" method implementation
        to return an empty response body.
        """
        super().create(request, *args, **kwargs)
        return Response({})


class UserInvitationTokenBasedRegistrationAPIView(generics.CreateAPIView):
    serializer_class = UserWithCompanyInvitationSerializer
    
    def get_serializer_context(self) -> dict:
        context = super().get_serializer_context()
        context['invitation_token'] = self.kwargs.get('invitation_token')
        
        return context
    
    def create(self, request: Request, *args, **kwargs) -> Response:
        """
        Overrides the default "create" method implementation
        to wrap the response body into a "user" field
        (for response format consistency).
        """
        response = super().create(request, *args, **kwargs)
        response.data = dict(user=response.data)
        
        return response


class ForgotPasswordAPIView(generics.UpdateAPIView):
    serializer_class = ForgotPasswordSerializer
    
    def get_object(self) -> User:
        """
        If a user with the provided email wasn't found, raises a custom API error,
        which encapsulates a 200 status code.
        This is done to prevent leaking information about
        whether a user with a particular email exists or not.
        """
        try:
            user = User.objects.get(email=self.request.data['email'])
        except (User.DoesNotExist, KeyError):
            raise APIExceptionWithCode200()
        
        return user
    
    def update(self, request: Request, *args, **kwargs) -> Response:
        """
        Overrides the default "update" method implementation
        to return an empty response body.
        """
        super().update(request, *args, **kwargs)
        return Response({})


class ResetPasswordAPIView(generics.UpdateAPIView):
    serializer_class = PasswordResetSerializer
    queryset = User.objects.all()
    
    def get_object(self) -> User:
        try:
            user = User.objects.validate_get_by_password_reset_token(
                self.kwargs.get('password_reset_token'))
            self.kwargs['user'] = user
        except ValidationError as e:
            raise serializers.ValidationError(e.message)
        
        return user
    
    def update(self, request: Request, *args, **kwargs) -> Response:
        """
        Overrides the default "update" method implementation to add user data
        and newly-issued access and refresh tokens to the response.
        """
        response = super().update(request, *args, **kwargs)
        user_instance = self.kwargs['user']
        response.data['user'] = UserWithTokenSerializer(user_instance).data
        
        return response


class UpdatePasswordAPIView(generics.UpdateAPIView):
    serializer_class = PasswordUpdateSerializer
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated,)
    
    def get_object(self) -> User:
        return self.request.user
    
    def update(self, request: Request, *args, **kwargs) -> Response:
        """
        Overrides the default "update" method implementation to add user data
        and newly-issued access and refresh tokens to the response.
        """
        response = super().update(request, *args, **kwargs)
        response.data['user'] = UserWithTokenSerializer(request.user).data
        
        return response


class LoginAPIView(TokenObtainPairView):
    """
    Inherits from TokenObtainPairView
    to override its default serializer_class class attribute.
    """
    serializer_class = LoginSerializer


class RefreshTokenAPIView(TokenRefreshView):
    """
    Inherits from TokenRefreshView
    to override its default serializer_class class attribute.
    """
    serializer_class = RefreshTokenSerializer
