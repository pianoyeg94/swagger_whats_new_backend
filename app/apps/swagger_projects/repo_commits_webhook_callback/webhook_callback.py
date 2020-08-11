from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from apps.swagger_projects.models import SwaggerFileChange
from .single_dispatch_classes import (
    RemoteVcsAccountIdFactory,
    SwaggerProjectInstanceIdFactory,
    RelatedCommitDetailsParser,
)

APP = apps.get_app_config('swagger_projects')
get_vcs_service_type = APP.get_vcs_service_type


class CallbackNotInitialized(Exception):
    """
    Raised if RepositoryCommitsWebhookCallback instance is called
    before "initialize_callback" instance method was called
    """


class RepositoryCommitsWebhookCallback:
    """
    Handles remote VCS respository commit webhook requests
    by parsing and interpreting the request body
    and saving the parsed result into a DB persisted
    SwaggerFileChange model instance.
    """
    
    def __init__(self, remote_vcs_service_header: str, data: dict):
        self.ignore_webhook = False
        self.callback_initialized = False
        self.remote_vcs_service = remote_vcs_service_header
        self.data = data
        self.remote_vcs_account_id = None
        self.swagger_project_id = None
        self.related_commit_details = None
        
        try:
            # set remote VCS service type depending on
            # VCS service type string representation
            self.remote_vcs_service_type = get_vcs_service_type(
                self.remote_vcs_service)
        except NotImplementedError:
            self.ignore_webhook = True
    
    @property
    def remote_vcs_service(self) -> str:
        return self._remote_vcs_service
    
    @remote_vcs_service.setter
    def remote_vcs_service(self, value) -> None:
        """
        Set remote VCS service type string representation
        depending on webhook header value
        """
        if value.startswith('GitHub'):
            self._remote_vcs_service = 'GH'
        elif value.startswith('Bitbucket'):
            self._remote_vcs_service = 'BB'
        else:
            self._remote_vcs_service = 'Not Implemented'
    
    def initialize_callback(self) -> None:
        """
        Parse and interprate webhook request body
        depending on remote VCS service type
        """
        try:
            if self.ignore_webhook:
                return
            
            self.remote_vcs_account_id = \
                RemoteVcsAccountIdFactory.get_instance_id(
                    self.remote_vcs_service_type,
                    data=self.data
                )
            
            self.swagger_project_id = \
                SwaggerProjectInstanceIdFactory.get_instance_id(
                    self.remote_vcs_service_type,
                    data=self.data,
                    remote_vcs_account_id=self.remote_vcs_account_id
                )
            
            self.related_commit_details = \
                RelatedCommitDetailsParser.get_related_commit_details(
                    self.remote_vcs_service_type,
                    data=self.data,
                    timestamp=str(timezone.now())
                )
        except ObjectDoesNotExist:
            self.ignore_webhook = True
        finally:
            self.callback_initialized = True
    
    def __call__(self) -> None:
        if not self.callback_initialized:
            raise CallbackNotInitialized(
                'Callback not initialized. Call initialize_callback()')
        
        if self.ignore_webhook or not self.related_commit_details:
            return
        
        # persist parsed and interprated webhook request body to DB
        # update or create a new SwaggerFileChange instance
        swagger_file_change, created = SwaggerFileChange.objects.get_or_create(
            swagger_project_id=self.swagger_project_id,
            swagger_file_changes={}
        )
        swagger_file_change.related_commit_details.append(
            self.related_commit_details)
        
        swagger_file_change.save()
