from requests import Response
import logging
from requests.exceptions import ConnectionError, HTTPError
from typing import Tuple, Union

from django.apps import apps

from .single_dispatch_classes import (
    AccessTokenEndpoint,
    AccessTokenPayload,
    AccessTokenResponseParser,
    AccessTokenRefreshEndpoint,
    AccessTokenRefreshPayload,
    AccessTokenRevokeEndpoint,
    AccessTokenRevokeHeaders,
    AccessTokenRevokePayload,
    RepoWebhookRegistrationEndpoint,
    RepoWebhookRegistrationPayload,
    RepoWebhookRegistrationHeaders,
    RepoWebhookRegistrationResponseParser,
    WebhookDeletionEndpoint,
    WebhookDeletionHeaders,
)

APP = apps.get_app_config("swagger_projects")
http = APP.http
get_vcs_service_type = APP.get_vcs_service_type
logger = logging.getLogger(__name__)


class VCSUtilityError(Exception):
    """Base VCS Utility exception"""

    default_message = 'A VCS Utility error has occured.'
    
    def __init__(self, message=None, *args, **kwargs):
        self.message = message or self.default_message
        args = (self.message, *args)
        super().__init__(*args, **kwargs)


class RepositoryDoesNotExistError(VCSUtilityError):
    default_message = 'Provided repository does not exist.'
    
    
class InvalidOrExpiredTemporaryOAuthTokenError(VCSUtilityError):
    default_message = 'Temporary OAuth token is invalid or has expired.'
    
    
class VCSAuthUtility:
    """
    Provides OAuth functionality to register,
    delete VCS accounts from "our" system
    
    Concrete method implementations depend on VCS service type
    provided to the __init__ method
    """
    
    def __init__(self, remote_vcs_service: str):
        self._remote_vcs_service_type = get_vcs_service_type(remote_vcs_service)
    
    def get_access_token(self, temp_token: str) -> Tuple[str, str]:
        response = self._trigger_access_token_request(temp_token)
        try:
            access_token, refresh_token = \
                self._parse_access_and_refresh_token_response(response)
        except KeyError:
            raise InvalidOrExpiredTemporaryOAuthTokenError()
        
        return access_token, refresh_token
    
    def refresh_access_token(self, refresh_token: str) -> Tuple[str, str]:
        response = self._trigger_refresh_access_token_request(refresh_token)
        access_token, refresh_token = \
            self._parse_access_and_refresh_token_response(response)
        
        return access_token, refresh_token
    
    def revoke_access_token(self, access_token: str) -> Union[Response, None]:
        endpoint = AccessTokenRevokeEndpoint.get_endpoint(
            self._remote_vcs_service_type)
        if not endpoint:
            return
        headers = AccessTokenRevokeHeaders.get_headers(
            self._remote_vcs_service_type)
        payload = AccessTokenRevokePayload.get_payload(
            self._remote_vcs_service_type,
            access_token=access_token
        )
        
        try:
            response = http.delete(endpoint, headers=headers, data=payload)
        except ConnectionError as e:
            logging.exception(e)
            raise
        
        return response
    
    def _trigger_access_token_request(self, temp_token: str) -> Response:
        endpoint = AccessTokenEndpoint.get_endpoint(self._remote_vcs_service_type)
        payload = AccessTokenPayload.get_payload(
            self._remote_vcs_service_type,
            temp_code=temp_token
        )
        
        try:
            response = http.post(endpoint, data=payload)
        except ConnectionError as e:
            logging.exception(e)
            raise
        
        return response
    
    def _trigger_refresh_access_token_request(self,
                                              refresh_token: str) -> Response:
        endpoint = AccessTokenRefreshEndpoint.get_endpoint(
            self._remote_vcs_service_type)
        payload = AccessTokenRefreshPayload.get_payload(
            self._remote_vcs_service_type,
            refresh_token=refresh_token
        )
        
        try:
            response = http.post(endpoint, data=payload)
        except ConnectionError as e:
            logging.exception(e)
            raise
        
        return response

    def _parse_access_and_refresh_token_response(self, response: Response) -> Tuple[str, ...]:
        access_token, refresh_token = AccessTokenResponseParser.get_tokens(
            self._remote_vcs_service_type,
            response=response
        )
    
        return access_token, refresh_token


class VCSWebhookUtiltity:
    """
    Provides OAuth functionality to integrate swagger projects
    with VCS repository webhooks
    
    Concrete method implementations depend on VCS service type
    provided to the __init__ method
    """
    
    def __init__(self, remote_vcs_service: str):
        self._remote_vcs_service_type = get_vcs_service_type(remote_vcs_service)
    
    def register_repo_webhook(self, vcs_account_name: str,
                              remote_repo_name: str,
                              access_token: str) -> str:
        response = self._trigger_repo_webhook_registration_request(
            vcs_account_name=vcs_account_name,
            remote_repo_name=remote_repo_name,
            access_token=access_token
        )
        try:
            response.raise_for_status()
        except HTTPError:
            raise RepositoryDoesNotExistError()
        
        webhook_id = self._parse_webhook_registration_response(response)
        
        return webhook_id
    
    def revoke_repo_webhook(self, vcs_account_name: str, webhook_id: str,
                            remote_repo_name: str, access_token: str) -> Response:
        endpoint = WebhookDeletionEndpoint.get_endpoint(
            self._remote_vcs_service_type,
            account_name=vcs_account_name,
            repo_name=remote_repo_name,
            webhook_id=webhook_id,
        )
        headers = WebhookDeletionHeaders.get_headers(
            self._remote_vcs_service_type,
            access_token=access_token
        )
        
        try:
            response = http.delete(endpoint, headers=headers)
        except ConnectionError as e:
            logging.exception(e)
            raise
        
        return response
    
    def _trigger_repo_webhook_registration_request(self, vcs_account_name: str,
                                                   remote_repo_name: str,
                                                   access_token: str) -> Response:
        endpoint = RepoWebhookRegistrationEndpoint.get_endpoint(
            self._remote_vcs_service_type,
            account_name=vcs_account_name,
            repo_name=remote_repo_name,
        )
        payload = RepoWebhookRegistrationPayload.get_payload(
            self._remote_vcs_service_type)
        headers = RepoWebhookRegistrationHeaders.get_headers(
            self._remote_vcs_service_type,
            access_token=access_token
        )
        
        try:
            response = http.post(endpoint, data=payload, headers=headers)
        except ConnectionError as e:
            logging.exception(e)
            raise
        
        return response
    
    def _parse_webhook_registration_response(self, response: Response) -> str:
        webhook_id = RepoWebhookRegistrationResponseParser.get_webhook_id(
            self._remote_vcs_service_type,
            response=response
        )
        
        return webhook_id
