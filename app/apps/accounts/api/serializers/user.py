from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)

from shared.validators import FieldsEqualityValidator
from apps.accounts.models import UserProfile, CompanyMembership
from apps.accounts.api.validators import (
    CompanyInvitationTokenValidator,
    PasswordValidator,
    PermissionSetValidator,
)

User = get_user_model()


class CompanyMembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyMembership
        fields = ('id', 'is_company_owner', 'permissions', 'job_title')
        read_only_fields = ('id', 'is_company_owner', 'permissions')


class UserWithCompanyMembershipSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    company_membership = CompanyMembershipSerializer()
    
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name',
                  'last_name', 'company_membership')
        read_only_fields = ('id',)


class UserWithTokenSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(write_only=True, required=True)
    password_confirm = serializers.CharField(write_only=True, required=True)
    company_membership = CompanyMembershipSerializer()
    token = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name',
                  'password', 'password_confirm', 'email_confirmed',
                  'company_membership', 'token')
        read_only_fields = ('id', 'email_confirmed', 'token')
        validators = [
            FieldsEqualityValidator(
                fields=['password', 'password_confirm'],
                message='Passwords do not match'
            )
        ]
    
    def get_token(self, user: User) -> dict:
        return user.jwt_token


class UserWithCompanyInvitationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(write_only=True, required=True)
    password_confirm = serializers.CharField(write_only=True, required=True)
    company_membership = CompanyMembershipSerializer()
    token = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name',
                  'password', 'password_confirm', 'email_confirmed',
                  'company_membership', 'token')
        read_only_fields = ('id', 'email_confirmed', 'token')
        validators = [
            CompanyInvitationTokenValidator(),
            FieldsEqualityValidator(
                fields=['password', 'password_confirm'],
                message='Passwords do not match'
            )
        ]
    
    def get_token(self, user: User) -> dict:
        return user.jwt_token
    
    def create(self, validated_data: dict) -> User:
        company_invitation = self.context['company_invitation']
        company = company_invitation.company
        company_membership = validated_data.pop('company_membership')
        validated_data.pop('password_confirm')
        
        user = User.objects.create_company_user(
            user_data=validated_data,
            company=company,
            company_invitation=company_invitation,
            company_membership=company_membership,
        )
        
        return user


class ConfirmEmailAddressSerializer(serializers.Serializer):
    
    def validate(self, data: dict) -> dict:
        try:
            self.context['request'].user.validate_email_confirmation_token(
                self.context['email_confirmation_token'])
        except ValidationError as e:
            raise serializers.ValidationError(e.message)
        
        return data
    
    def update(self, instance: User, validated_data: dict) -> User:
        instance.email_confirmed = True
        instance.save()
        
        return instance


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    
    def update(self, instance: User, validated_data: dict) -> User:
        instance.set_password_reset_token()
        instance.save(update_fields=['password_reset_token',
                                     'password_reset_expires'])
        return instance


class PasswordResetSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('password', 'password_confirm')
        validators = [
            FieldsEqualityValidator(
                fields=['password', 'password_confirm'],
                message='Passwords do not match'
            )
        ]
    
    def update(self, instance: User, validated_data: dict) -> User:
        instance.reset_password(validated_data['password'])
        instance.save()
        
        return instance


class PasswordUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    current_password = serializers.CharField(
        write_only=True,
        validators=[PasswordValidator()]
    )
    
    class Meta:
        model = User
        fields = ('password', 'password_confirm', 'current_password')
        validators = [
            FieldsEqualityValidator(
                fields=['password', 'password_confirm'],
                message='Passwords do not match'
            )
        ]
    
    def update(self, instance: User, validated_data: dict) -> User:
        instance.set_password(validated_data['password'])
        instance.save()
        
        return instance


class LoginSerializer(TokenObtainPairSerializer):
    
    def validate(self, data: dict) -> dict:
        """Overrides default implementation to add user details to response."""
        super().validate(data)
        data = dict(user=UserWithTokenSerializer(self.user).data)
        
        return data


class RefreshTokenSerializer(TokenRefreshSerializer):
    
    def validate(self, data: dict) -> dict:
        """
        Overrides default implementation to add user details
        and token expiration datetime to response.
        """
        data = super().validate(data)
        access_token_expires_in = \
            settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds() * 1000
        data = dict(
            access=str(data['access']),
            expires_in=access_token_expires_in
        )
        
        return data


class UpdateMeSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    company_membership = CompanyMembershipSerializer()
    
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name',
                  'company_membership', 'email_confirmed')
        read_only_fields = ('id', 'email_confirmed',)
    
    def update(self, instance: User, validated_data: dict) -> User:
        current_email = instance.email
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        
        company_membership = instance.company_membership
        company_membership.job_title = validated_data.get('company_membership').get(
            'job_title',
            company_membership.job_title
        )
        
        # if user changed email, set "email_confirmed" to false
        # and send email address confirmation email
        if current_email != validated_data.get('email'):
            instance.email_confirmed = False
            instance.save(update_fields=['email'])
        else:
            instance.save()
        
        company_membership.save()
        
        return instance


class UserProfilePhotoSerializer(serializers.ModelSerializer):
    profile_photo = serializers.ImageField()
    
    class Meta:
        model = UserProfile
        fields = ('profile_photo',)


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('id', 'phone_number', 'skype', 'profile_photo')
        read_only_fields = ('id', 'profile_photo',)


class CompanyMembershipPermissionsSerializer(serializers.ModelSerializer):
    permissions = serializers.IntegerField(validators=[PermissionSetValidator()])
    
    class Meta:
        model = CompanyMembership
        fields = ('id', 'permissions')


class CompanyMembershipPermissionsListSerializer(serializers.Serializer):
    register_vcs_accounts = serializers.IntegerField(read_only=True)
    create_swagger_projects = serializers.IntegerField(read_only=True)
    invite_new_users = serializers.IntegerField(read_only=True)


class UserWithCompanyMembershipAndProfileSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()
    company_membership = CompanyMembershipSerializer()
    
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name',
                  'company_membership', 'profile')
        read_only_fields = ('id', 'email',)
