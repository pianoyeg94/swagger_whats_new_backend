import logging
from json import JSONDecodeError
from requests.exceptions import ConnectionError
from typing import Union

from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from django.apps import apps
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.indexes import GinIndex

from apps.accounts.models import Company
from .vcs import RemoteVCSAccount
from apps.swagger_projects.vcs_utility import (
    vcs_webhook_util_factory,
    VCSWebhookUtiltity,
    RepositoryDoesNotExistError
)

APP = apps.get_app_config('swagger_projects')
http = APP.http
logger = logging.getLogger(__name__)


class SwaggerFileManager(models.Manager):
    
    def validate_create(self, swagger_project_instance: 'SwaggerProject') -> Union['SwaggerFile', None]:
        """
        This method pulls
         and validates swagger files
        associated with a particluar Swagger Project instance.
        
        If the downloaded swagger file is valid, it saves the new Swagger File
        instance to DB, otherwise
        it deletes its associated Swagger Project and returns abroptly.
        """
        try:
            swagger_file_response = http.get(
                swagger_project_instance.swagger_file_url)
        except ConnectionError as e:
            logger.exception(e)
            swagger_project_instance.delete()
            return
        
        # if the response body is not json encoded return abroptly
        # and delete the associated Swagger Project instance.
        try:
            swagger_file = swagger_file_response.json()
        except JSONDecodeError:
            swagger_project_instance.delete()
            return
        
        # if the parsed json body doesn't adhere to
        # the expected swagger file format, return abroptly
        # and delete the associated Swagger Project instance
        try:
            swagger_file['swagger']
            swagger_file['info']
            swagger_file['host']
            swagger_file['schemes']
            swagger_file['paths']
            swagger_file['definitions']
        except KeyError:
            swagger_project_instance.delete()
            return
        
        swagger_file_instance = self.create(
            swagger_file=swagger_file,
            swagger_project=swagger_project_instance
        )
        
        return swagger_file_instance


class SwaggerProject(models.Model):
    """
    This Model represents a single Swagger Project entity in the database.
    
    Swagger Projects can be integrated with Remote VCS Accounts
    to keep track of commits that triggered particular swagger file changes.
    """
    
    project_name = models.CharField(
        max_length=150,
        null=False,
        verbose_name='Swagger Project Name'
    )
    use_vcs = models.BooleanField(
        default=True,
        verbose_name='Swagger Project Uses a VCS Account'
    )
    remote_repo_name = models.CharField(
        max_length=150,
        null=True,
        default=None,
        verbose_name='Remote VCS Repository Name'
    )
    remote_repo_branch = models.CharField(
        max_length=150,
        null=True,
        default=None,
        verbose_name='Remote VCS Repository Branch'
    )
    swagger_file_url = models.URLField(
        max_length=300,
        null=False,
        verbose_name='Swagger File URL'
    )
    webhook_id = models.CharField(
        max_length=300,
        null=True,
        default=None,
        verbose_name='Remote VCS Repository Webhook ID'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    remote_vcs_account = models.ForeignKey(
        RemoteVCSAccount,
        on_delete=models.CASCADE,
        null=True,
        default=None,
        related_name='swagger_projects',
        verbose_name='Associated Remote VCS Account'
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='swagger_projects',
        verbose_name='Owned by Company'
    )
    project_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='swagger_projects',
        verbose_name='Swagger Project Owner'
    )
    
    class Meta:
        db_table = 'swagger_projects'
        indexes = [
            # for pagination efficiency
            models.Index(
                fields=['created_at', 'company'],
                name='idx_swg_prj_created_at'
            ),
            # for Rest API "icontains - LIKE" filtering efficiency
            GinIndex(
                fields=['remote_repo_name', 'company'],
                name='idx_swg_prj_remote_repo_name',
            ),
            # for Rest API "icontains - LIKE" filtering efficiency
            GinIndex(
                fields=['remote_repo_branch', 'company'],
                name='idx_swg_prj_remote_repo_branch',
            )
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['remote_vcs_account', 'remote_repo_name',
                        'remote_repo_branch'],
                name='unique_remote_repo_branch',
            ),
            models.UniqueConstraint(
                fields=['project_name', 'company'],
                name='unique_swagger_project_name'
            )
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._vcs_webhook_util = None
    
    @property
    def vcs_webhook_util(self) -> VCSWebhookUtiltity:
        """
        A lazy loaded and cached property due to the fact
        that it requires a database lookup (remote_vcs_service).
        
        Exposes an instance of the VCS Webhook utility class.
        """
        if self._vcs_webhook_util is None:
            self._vcs_webhook_util = vcs_webhook_util_factory.get_util(
                self.remote_vcs_account.remote_vcs_service)
        return self._vcs_webhook_util
    
    def set_webhook_id(self) -> None:
        # if a particular Swagger Project instance
        # is not integrated with a VCS Account, return abroptly.
        if not self.use_vcs:
            return
        
        webhook_id = SwaggerProject.objects.filter(
            remote_repo_name=self.remote_repo_name
        ).values_list('webhook_id', flat=True).first()
        
        # Webhook ID's are associated with repositories.
        # If some other project is associated with the same repository
        # just use its webhook ID.
        if webhook_id:
            self.webhook_id = webhook_id
            return
        
        try:
            self.webhook_id = self.vcs_webhook_util.register_repo_webhook(
                vcs_account_name=self.remote_vcs_account.account_name,
                remote_repo_name=self.remote_repo_name,
                access_token=self.remote_vcs_account.unencrypted_access_token
            )
        except RepositoryDoesNotExistError as e:
            raise ValidationError(e.message)
    
    def delete_repo_webhook(self) -> None:
        # if a particular Swagger Project instance
        # is not integrated with a VCS Account, return abroptly.
        if not self.use_vcs:
            return
        
        webhook_id = SwaggerProject.objects.filter(
            remote_repo_name=self.remote_repo_name
        ).values_list('webhook_id', flat=True).first()
        
        # If some other project is asscociated with the same repository,
        # chances are it's using the same Webhook ID. Do not revoke this webhook.
        if webhook_id:
            return
        
        self.vcs_webhook_util.revoke_repo_webhook(
            vcs_account_name=self.remote_vcs_account.account_name,
            webhook_id=self.webhook_id,
            remote_repo_name=self.remote_repo_name,
            access_token=self.remote_vcs_account.unencrypted_access_token
        )
    
    def __str__(self):
        return self.project_name


class SwaggerFile(models.Model):
    """
    This model represents a single Swagger File
    associated with a particular Swagger Project.
    
    Swagger files are stored directly in the database
    in jsonb format (field "swagger_file").
    """
    
    swagger_file = JSONField(null=False, verbose_name='Swagger File')
    swagger_project = models.OneToOneField(
        SwaggerProject,
        on_delete=models.CASCADE,
        related_name='swagger_file',
        verbose_name='Associated Swagger Project'
    )
    
    objects = SwaggerFileManager()
    
    class Meta:
        db_table = 'swagger_files'
    
    def __str__(self):
        return f'{self.swagger_project.project_name}_swagger_file'


class SwaggerFileChange(models.Model):
    """
    This model represents a single Swagger File Change entity
    associated with a particular Swagger Project.
    
    Swagger file changes are stored directly in the database
    in jsonb format (field "swagger_file_changes").
    
    Each swagger file change representation is devided into 2 sections:
    1) Additions - added endpoints, methods, etc.
    2) Removals - removed endpoints, methods, etc.
    
    Each section in turn is devided into 4 subsections:
    1) Endpoints - added, removed API endpoints.
    2) Methods - added, removed methods for particular endpoints.
    3) Contracts - added, removed contracts.
    4) Contract Properties - added, removed properties in a particular contract.
    
    There is no need for normalization,
    "swagger_file_changes" are not planned to be aggregated
    or used in any sort of filter.
    
    If this is going to change sometime in the future,
    it will be easy to use postgres' jsonb aggregation functionality
    instead of normalization.
    """
    
    related_commit_details = JSONField(
        null=False,
        default=list,
        verbose_name='Commits that presumably triggered this Swagger File Change'
    )
    swagger_file_changes = JSONField(
        default=dict,
        verbose_name='Swagger File Change Details'
    )
    changes_added_at = models.DateTimeField(
        db_index=True,
        null=True,
        default=None,
        verbose_name='Swagger File Changes Added At'
    )
    swagger_project = models.ForeignKey(
        SwaggerProject,
        on_delete=models.CASCADE,
        related_name='swagger_file_changes',
        verbose_name='Associated Swagger Project'
    )
    
    class Meta:
        db_table = 'swagger_file_changes'
    
    def __str__(self):
        return f'{self.swagger_project.project_name}_' \
               f'swagger_file_change_{self.changes_added_at}'


class SwaggerFileChangeComment(models.Model):
    """
    This model represents a single comment instance
    associated with a particular Swagger File Change.
    """
    
    comment_text = models.TextField(verbose_name='Comment Text')
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    comment_author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='swagger_file_change_comments',
        verbose_name='Comment Author'
    )
    swagger_file_change = models.ForeignKey(
        SwaggerFileChange,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Associated Swagger File Change'
    )
    
    class Meta:
        db_table = 'swagger_file_changes_comments'
    
    def __str__(self):
        return self.comment_text
