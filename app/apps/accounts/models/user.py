import os
import datetime
from typing import TYPE_CHECKING

from django.core import signing
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFill
from rest_framework_simplejwt.tokens import RefreshToken

from utils.functions import sha256_hasher

if TYPE_CHECKING:
    from .company import Company, CompanyInvitation, CompanyMembership


def photo_path(instance: 'UserProfile', filename: str) -> str:
    """
    Utility function used to generate image names.
    Used in combination with imagekit's ProcessedImageField.
    
    Format: timestamp-hashed_original_image_name.file_extension
    """
    basefilename, file_extension = os.path.splitext(filename)
    hash_ = sha256_hasher(filename + str(instance.id))
    timestamp = timezone.now()
    return f'user_photos/{timestamp}-{hash_}.{file_extension}'


class UserManager(BaseUserManager):
    """
    Inherits direcly from BaseUserManager.
    Due to the fact that custom company membership permissions are used,
    inheritance from django's UserManager is not required.
    """
    
    use_in_migrations = True

    def _create_user(self, email: str, password: str, **extra_fields) -> 'User':
        """
        Create and save a user with the given email, and password.
        
        This method is taken straight from django's UserManager class.
        Tweaked to omit the username.
        """
        if not email:
            raise ValueError('The given email must be set')
        if not password:
            raise ValueError('The given password must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        
        return user

    def create_user(self, email: str, password: str, **extra_fields) -> 'User':
        return self._create_user(email, password, **extra_fields)

    @transaction.atomic
    def create_company_user(self, company: 'Company',
                            company_membership: 'CompanyMembership',
                            user_data: dict,
                            company_invitation: 'CompanyInvitation') -> 'User':
        """
        Creates a new user associated with a particular company
        using a CompanyInvitation instance to decide
        which company this user belongs to.
        """
        user = self.create_user(**user_data)
        company.user.add(
            user,
            through_defaults={
                'job_title': company_membership['job_title'],
                'permissions': company_invitation.desired_company_permissions,
            }
        )
        company_invitation.delete()

        return user

    def validate_get_by_password_reset_token(self, reset_token: str) -> 'User':
        """
        Finds a user via his password reset token.
        If the token is expired or such a user doesn't exist in the system,
        a validation error is raised.
        """
        hashed_reset_token = sha256_hasher(reset_token)
        try:
            user = self.get(
                password_reset_token=hashed_reset_token,
                password_reset_expires__gt=timezone.now(),
            )
        except self.model.DoesNotExist:
            raise ValidationError('Token is invalid or has expired.')

        return user


class User(AbstractBaseUser):
    """
    This model represents a single User entity in the database.
    
    Inherits from AbstractBaseUser to get rid of unrequired fields and methods,
    including the "username" field.
    
    Users and companies form a many-to-many relationship.
    This relation uses a custom "through" model - CompanyMembership.
    
    Although a many-to-many relationship is used,
    currently a single user can only be associated with a single company.
    This may change in the future.
    """
    
    email = models.EmailField(
        max_length=150,
        unique=True,
        verbose_name='Email Address'
    )
    first_name = models.CharField(
        max_length=150,
        null=False,
        verbose_name='First Name'
    )
    last_name = models.CharField(
        max_length=150,
        null=False,
        verbose_name='Last Name'
    )
    email_confirmed = models.BooleanField(
        default=True,
        verbose_name='User Comfirmed His Email'
    )
    password_changed_at = models.DateTimeField(
        null=True,
        default=None,
        verbose_name='Password Changed At'
    )
    password_reset_token = models.CharField(
        max_length=250,
        null=True,
        default=None,
        verbose_name='Password Reset Token'
    )
    password_reset_expires = models.DateTimeField(
        null=True,
        default=None,
        verbose_name='Password Reset Token Expires At'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )

    USERNAME_FIELD = 'email'

    PASSWORD_RESET_TOKEN_EXPIRES_IN = \
        settings.PASSWORD_RESET_TOKEN_EXPIRES_IN_MINUTES

    ACCESS_TOKEN_EXPIRES_IN = \
        settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds() * 1000
    
    REFRESH_TOKEN_EXPIRES_IN = \
        settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds() * 1000

    objects = UserManager()

    class Meta:
        db_table = 'users'
        indexes = [
            # for pagination efficiency
            models.Index(
                fields=['created_at'],
                name='idx_users_created_at'
            )
        ]

    # The next 4 properties hide the underlying many-to-many nature
    # of user-company relations behind a convenient api.
    @property
    def company(self) -> 'Company':
        return self.companies.first()

    @property
    def company_id(self) -> int:
        return self.companies.values_list('id', flat=True).first()

    @property
    def company_membership(self) -> 'CompanyMembership':
        return self.company_memberships.first()

    @property
    def company_membership_id(self) -> int:
        return self.company_memberships.values_list('id', flat=True).first()

    @property
    def email_confirmation_token(self) -> str:
        return signing.dumps({'id': self.id})

    @property
    def unhashed_password_reset_token(self) -> str:
        return signing.dumps({'id': self.id})

    @property
    def jwt_token(self) -> dict:
        refresh = RefreshToken.for_user(self)
        token = {
            'refresh': {
                'token': str(refresh),
                'expires_in': self.REFRESH_TOKEN_EXPIRES_IN,
            },
            'access': {
                'token': str(refresh.access_token),
                'expires_in': self.ACCESS_TOKEN_EXPIRES_IN,
            }
        }

        return token

    def set_password_reset_token(self) -> None:
        self.password_reset_token = sha256_hasher(self.unhashed_password_reset_token)
        self.password_reset_expires = timezone.now() + datetime.timedelta(
            minutes=self.PASSWORD_RESET_TOKEN_EXPIRES_IN)

    def reset_password(self, password: str) -> None:
        self.set_password(password)
        self.password_reset_token = None
        self.password_reset_expires = None
        self.password_changed_at = timezone.now()

    def clear_password_reset_token(self) -> None:
        self.password_reset_token = None
        self.password_reset_expires = None

    def update_password(self, password: str) -> None:
        self.reset_password(password)
        self.password_changed_at = timezone.now()

    def validate_email_confirmation_token(self, confirmation_token: str) -> None:
        error_message = \
            'Email confirmation token is invalid or email already confirmed.'
        try:
            user_id = signing.loads(confirmation_token)['id']
        except signing.BadSignature:
            raise ValidationError(error_message)

        if user_id != self.id or self.email_confirmed:
            raise ValidationError(error_message)


class UserProfile(models.Model):
    """
    This model represents a single User Profile entity in the database.
    Has a one-to-one mapping with its corresponding user.
    """
    
    phone_number = models.CharField(
        max_length=15,
        null=True,
        default=None,
        verbose_name='Phone Number'
    )
    skype = models.CharField(
        max_length=150,
        null=True,
        default=None,
        verbose_name='Skype'
    )
    # Image upload and storage will be refactored to use blob storages
    # (AWS S3 or gcloud buckets) and take advantage of presigned urls.
    # Currently images are stored in "production"
    # on an nfs server pod within a kubernetes cluster and served by nginx.
    profile_photo = ProcessedImageField(
        upload_to=photo_path,
        processors=[ResizeToFill(500, 500)],
        format='JPEG',
        options={'quality': 60},
        max_length=300,
        null=True,
        verbose_name='Profile Photo'
    )
    profile_owner = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='User Associated With This Profile'
    )

    class Meta:
        db_table = 'user_profiles'

    def __str__(self):
        return self.profile_owner.get_username()
