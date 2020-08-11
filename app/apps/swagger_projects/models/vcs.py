from django.core import signing
from django.core.exceptions import ValidationError
from django.db import models

from apps.accounts.models import Company
from apps.swagger_projects.vcs_utility import (
    vcs_auth_util_factory,
    VCSAuthUtility,
    InvalidOrExpiredTemporaryOAuthTokenError
)


class RemoteVCSAccount(models.Model):
    """
    This Model represents a Remote Version Control System Account
    registered in "our" system via OAuth.
    """
    
    GITHUB = 'GH'
    BITBUCKET = 'BB'
    REMOTE_VCS_SERVICE_CHOICES = (
        (GITHUB, 'GitHub'),
        (BITBUCKET, 'Bitbucket')
    )
    
    USER = 'U'
    ORGANIZATION = 'O'
    ACCOUNT_TYPE_CHOICES = (
        (USER, 'User'),
        (ORGANIZATION, 'Organization')
    )
    
    account_name = models.CharField(
        max_length=150,
        null=False,
        verbose_name='Remote VCS Account Name'
    )
    access_token = models.CharField(
        max_length=300,
        null=False,
        verbose_name='Remote VCS Account OAuth Access Token'
    )
    refresh_token = models.CharField(
        max_length=300,
        null=True,
        default=None,
        verbose_name='Remote VCS Account OAuth Refresh Token'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    remote_vcs_service = models.CharField(
        max_length=2,
        choices=REMOTE_VCS_SERVICE_CHOICES,
        null=False,
        verbose_name='Remote VCS Service Provider'
    )
    account_type = models.CharField(
        max_length=1,
        choices=ACCOUNT_TYPE_CHOICES,
        null=False,
        verbose_name='Remote VCS Account Type'
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='remote_vcs_accounts',
        verbose_name='Owned by Company'
    )
    
    class Meta:
        db_table = 'remote_vcs_accounts'
        indexes = [
            # for pagination efficiency
            models.Index(
                fields=['created_at', 'company'],
                name='idx_vcs_accs_created_at'
            )
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['remote_vcs_service', 'company', 'account_name'],
                name='unique_vcs_account_name'
            )
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._vcs_auth_util = None
    
    @property
    def vcs_auth_util(self) -> VCSAuthUtility:
        """
        A lazy loaded and cached property due to the fact
        that it requires a database lookup (remote_vcs_service).
        
        Exposes an instance of the VCS OAuth utility class.
        """
        if self._vcs_auth_util is None:
            self._vcs_auth_util = vcs_auth_util_factory.get_util(
                self.remote_vcs_service)
        return self._vcs_auth_util
    
    @property
    def unencrypted_refresh_token(self) -> str:
        return signing.loads(self.refresh_token)['refresh_token']
    
    @property
    def unencrypted_access_token(self) -> str:
        return signing.loads(self.access_token)['access_token']
    
    def set_and_validate_access_token(self, temp_token: str) -> None:
        try:
            access_token, refresh_token = \
                self.vcs_auth_util.get_access_token(temp_token)
        except InvalidOrExpiredTemporaryOAuthTokenError as e:
            raise ValidationError(e.message)
        
        self._set_access_token(access_token)
        self._set_refresh_token(refresh_token)
    
    def refresh_access_token(self) -> None:
        # if a particular model instance doesn't have a refresh token,
        # return abroptly (depends on external VCS OAuth implementations)
        if not self.refresh_token:
            return
        
        access_token, refresh_token = \
            self.vcs_auth_util.refresh_access_token(self.refresh_token)
        
        self._set_access_token(access_token)
        self._set_refresh_token(refresh_token)
    
    def revoke_access_token(self) -> None:
        self.vcs_auth_util.revoke_access_token(self.unencrypted_access_token)
    
    def _set_access_token(self, access_token: str) -> None:
        self.access_token = signing.dumps({'access_token': access_token})
    
    def _set_refresh_token(self, refresh_token: str) -> None:
        self.refresh_token = (
            refresh_token
            if refresh_token is None
            else signing.dumps({'refresh_token': refresh_token})
        )
    
    def __str__(self):
        return f'{self.remote_vcs_service}_{self.account_name}'
