import datetime
from typing import Tuple

from django.core import signing
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model

from shared.abstract_models import SingletonModel
from utils.functions import sha256_hasher

User = get_user_model()


class CompanyManager(models.Manager):
    
    @transaction.atomic
    def create_company_account(self,
                               company_data: dict,
                               user_data: dict,
                               membership_data: dict) -> Tuple['Company', User]:
        """
        Given a set of company, user and company membership data
        create a user (company owner) and company,
        link them through a company membership instance.
        """
        company = self.create(company_name=company_data['company_name'])
        
        user = User.objects.create_user(
            email=user_data['email'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            password=user_data['password'],
            email_confirmed=False
        )
        
        company.user.add(
            user,
            through_defaults={
                'is_company_owner': True,
                'job_title': membership_data['job_title'],
                'permissions': CompanyMembership.PERMISSIONS_ENUM.all_permissions
            }
        )
        
        return company, user


class CompanyInvitationManager(models.Manager):

    def validate_get_by_invitation_token(self, invitation_token: str) -> 'CompanyInvitation':
        """
        Find company invitations via invitation tokens.
        If the token is expired
        or such an invitation doesn't exist in the system,
        raise a validation error.
        """
        encrypted_invitation_token = sha256_hasher(invitation_token)
        try:
            invitation_instance = self.get(
                invitation_token=encrypted_invitation_token,
                invitation_expires__gt=timezone.now(),
            )
        except self.model.DoesNotExist:
            raise ValidationError('Token is invalid or has expired.')
        
        return invitation_instance


class CompanyMembershipManager(models.Manager):
    
    def validate_permissions_set(self, permission_set: int) -> None:
        """
        Validate that a provided set of permissions
        represented by an integer value
        is equal to one of the possible permission permutations
        (sum of permutations to be exact).
        """
        permission_combinations_lst = \
            self.model.PERMISSIONS_ENUM.all_possible_permission_combinations
        permission_combinations_lst.append(0)  # no permissions
        
        if permission_set not in permission_combinations_lst:
            raise ValidationError('Invalid permissions provided.')


class Company(models.Model):
    """
    This model represents a single Company entity in the database.

    Users and companies form a many-to-many relationship.
    This relation uses a custom "through" model - CompanyMembership.

    Although a many-to-many relationship is used,
    currently a single user can only be associated with a single company.
    This may change in the future.
    """
    
    company_name = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='Company Name'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    user = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='CompanyMembership',
        through_fields=('company', 'user'),
        related_name='companies',
        verbose_name='Company Member'
    )
    
    objects = CompanyManager()
    
    class Meta:
        db_table = 'companies'
    
    @transaction.atomic
    def delete_company_account(self) -> None:
        """When a company is deleted delete all its memebers"""
        self.user.all().delete()
        self.delete()
    
    def __str__(self):
        return self.company_name


class CompanyMembershipPermissions(SingletonModel):
    """
    This is a "singleton" model which shouldn't be modified programmatically
    during the application's lifecycle.
    Is used to store values for the company membership permissions enum.
    Loaded from the database and transformed into an enum at application startup.
    
    These permissions are very lightweight
    and are represented by powers of 2 to leverage the power of bitwise operators.
    """
    
    register_vcs_account = models.IntegerField(
        default=1,
        verbose_name='Company Member is allowed to register New VCS Accounts'
    )
    create_swagger_projects = models.IntegerField(
        default=2,
        verbose_name='Company Member is allowed to create New Swagger Projects'
    )
    invite_new_users = models.IntegerField(
        default=4,
        verbose_name='Company Member is allowed to invite New Users'
    )
    
    class Meta:
        db_table = 'company_membership_permissions'


class CompanyMembership(models.Model):
    """
    This is a custom "through" model that links users and companies together.
    Provides extended functionality
    like company membership permissions validation and modification.
    """
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    is_company_owner = models.BooleanField(
        default=False,
        verbose_name='Company Member owns this Company'
    )
    job_title = models.CharField(
        max_length=150,
        null=False,
        verbose_name='Company Member\'s Job Title'
    )
    permissions = models.IntegerField(
        default=0,
        verbose_name='Company Membership Permissions'
    )
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name='Company associated with this Membership'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='company_memberships',
        verbose_name='User associated with this Membership.'
    )
    
    # populated from the database at application startup
    PERMISSIONS_ENUM = None
    
    objects = CompanyMembershipManager()
    
    class Meta:
        db_table = 'company_memberships'
    
    def has_permission(self, perm: int) -> bool:
        """
        Company membership permissions use powers of 2
        which makes it very convenient to validate them
        with the help of the bitwise "and" operator.
        """
        return (self.permissions & perm) == perm
    
    def add_permission(self, perm: int) -> None:
        if not self.has_permission(perm):
            self.permissions += perm
    
    def remove_permission(self, perm: int) -> None:
        if self.has_permission(perm):
            self.permissions -= perm
    
    def reset_permissions(self) -> None:
        self.permissions = 0
    
    def add_all_permissions(self) -> None:
        """
        Replaces the current instance's membership permissions
        with a sum of all available permissions.
        """
        self.reset_permissions()
        self.permissions += self.PERMISSIONS_ENUM.all_permissions
    
    def __str__(self):
        return f'{self.company.company_name}_{self.user.get_username()}'


class CompanyInvitation(models.Model):
    """This model is used to manage user invitations"""
    
    email = models.EmailField(
        verbose_name='Email Address'
    )
    invitation_token = models.CharField(
        max_length=150,
        null=False,
        verbose_name='Hashed Company Invitation Token'
    )
    invitation_expires = models.DateTimeField(
        verbose_name='Company Invitation Token Expires At'
    )
    desired_company_permissions = models.IntegerField(
        default=0,
        verbose_name='Preassigned Company Membership Permissions'
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='invitations',
        verbose_name='Company associated with this Invitation'
    )
    
    INVITATION_TOKEN_EXPIRES_IN = \
        settings.COMPANY_INVITATION_TOKEN_EXPIRES_IN_MINUTES
    
    objects = CompanyInvitationManager()
    
    class Meta:
        db_table = 'company_invitations'
    
    def save(self, *args, **kwargs) -> None:
        """
        Overrides django model's default "save" method implementation
        to automatically hash and save the invitation token
        as well as set its expiration date and time.
        """
        self.invitation_expires = timezone.now() + datetime.timedelta(
            minutes=self.INVITATION_TOKEN_EXPIRES_IN)
        self.invitation_token = sha256_hasher(self.unhashed_invitation_token)
        super().save(*args, **kwargs)
    
    @property
    def unhashed_invitation_token(self) -> str:
        """
        Returns the invitation token in its unhashed state.
        This unhashed token is used in the invitation link.
        """
        return signing.dumps({'email': self.email})
    
    def __str__(self):
        return f'{self.company.company_name}_invited_{self.email}'
