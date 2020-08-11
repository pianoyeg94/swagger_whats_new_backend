import base64
import json
from functools import singledispatchmethod
from requests import Response
from typing import Dict, Tuple, Union

from django.conf import settings
from django.apps import apps

APP = apps.get_app_config('swagger_projects')
VCS_TYPES = APP.vcs_types
GHType = VCS_TYPES.GH.value
BBType = VCS_TYPES.BB.value
VCSTypes = Union[GHType, BBType]

"""
Container classes that use single dispatch methods
to provide details for http interaction with remote VCS service APIs.

Concrete implementations depend on specified VCS service types
(currently Github and Bitbucket integrations are supported)
"""

class AccessTokenEndpoint:
    @singledispatchmethod
    @staticmethod
    def get_endpoint(service_type: VCSTypes) -> str:
        raise NotImplementedError('Unsupported type')
    
    @staticmethod
    @get_endpoint.register
    def _(service_type: GHType) -> str:
        return 'https://github.com/login/oauth/access_token'
    
    @staticmethod
    @get_endpoint.register
    def _(service_type: BBType) -> str:
        return 'https://bitbucket.org/site/oauth2/access_token'


class AccessTokenPayload:
    @singledispatchmethod
    @staticmethod
    def get_payload(service_type: VCSTypes, *, temp_code: str) -> Dict[str, str]:
        raise NotImplementedError('Unsupported type')
    
    @staticmethod
    @get_payload.register
    def _(service_type: GHType, *, temp_code: str) -> Dict[str, str]:
        return {
            'client_id': settings.VCS_CREDENTIALS['GITHUB']['client_id'],
            'client_secret': settings.VCS_CREDENTIALS['GITHUB']['client_secret'],
            'code': temp_code,
        }
    
    @staticmethod
    @get_payload.register
    def _(service_type: BBType, *, temp_code: str) -> Dict[str, str]:
        return {
            'grant_type': 'authorization_code',
            'client_id': settings.VCS_CREDENTIALS['BITBUCKET']['client_id'],
            'client_secret': settings.VCS_CREDENTIALS['BITBUCKET'][
                'client_secret'],
            'code': temp_code,
        }


class AccessTokenResponseParser:
    @singledispatchmethod
    @staticmethod
    def get_tokens(service_type: VCSTypes, *,
                   response: Response) -> Tuple[str, Union[str, None]]:
        raise NotImplementedError('Unsupported type')
    
    @staticmethod
    @get_tokens.register
    def _(service_type: GHType, *,
          response: Response) -> Tuple[str, Union[str, None]]:
        return dict(param.split('=') for param in response.text.split('&'))[
                   'access_token'], None
    
    @staticmethod
    @get_tokens.register
    def _(service_type: BBType, *,
          response: Response) -> Tuple[str, Union[str, None]]:
        return response.json()['access_token'], response.json()['refresh_token']


class RepoWebhookRegistrationEndpoint:
    @singledispatchmethod
    @staticmethod
    def get_endpoint(service_type: VCSTypes, *,
                     account_name: str,
                     repo_name: str) -> str:
        raise NotImplementedError('Unsupported type')
    
    @staticmethod
    @get_endpoint.register
    def _(service_type: GHType, *, account_name: str, repo_name: str) -> str:
        return '/'.join(
            ('https://api.github.com/repos', account_name, repo_name, 'hooks')
        )
    
    @staticmethod
    @get_endpoint.register
    def _(service_type: BBType, *, account_name: str, repo_name: str) -> str:
        return '/'.join(
            ('https://api.bitbucket.org/2.0/repositories', account_name,
             repo_name, 'hooks')
        )


class RepoWebhookRegistrationPayload:
    @singledispatchmethod
    @staticmethod
    def get_payload(service_type: VCSTypes) -> str:
        raise NotImplementedError('Unsupported type')
    
    @staticmethod
    @get_payload.register
    def _(service_type: GHType) -> str:
        return json.dumps(
            {
                'name': 'web',
                'active': True,
                'events': ['push'],
                'config': {
                    'url': 'https://'
                           f'{settings.ALLOWED_HOSTS[0]}/v1'
                           '/swagger-projects/webhook-callback/',
                    'content_type': 'json',
                    'insecure_ssl': '0',
                }
            }
        )
    
    @staticmethod
    @get_payload.register
    def _(service_type: BBType) -> str:
        return json.dumps(
            {
                'description': 'Webhook Description',
                'url': f'http://'
                       f'{settings.ALLOWED_HOSTS[0]}/v1'
                       f'/swagger-projects/webhook-callback/',
                'active': True,
                'events': ['repo:push']
            }
        )


class RepoWebhookRegistrationHeaders:
    @singledispatchmethod
    @staticmethod
    def get_headers(service_type: VCSTypes, *, access_token: str) -> Dict[str, str]:
        raise NotImplementedError('Unsupported type')
    
    @staticmethod
    @get_headers.register
    def _(service_type: GHType, *, access_token: str) -> Dict[str, str]:
        return {'Authorization': f'Bearer {access_token}'}
    
    @staticmethod
    @get_headers.register
    def _(service_type: BBType, *, access_token: str) -> Dict[str, str]:
        return {'Authorization': f'Bearer {access_token}'}


class RepoWebhookRegistrationResponseParser:
    @singledispatchmethod
    @staticmethod
    def get_webhook_id(service_type: VCSTypes, *, response: Response) -> str:
        raise NotImplementedError('Unsupported type')
    
    @staticmethod
    @get_webhook_id.register
    def _(service_type: GHType, *, response: Response) -> str:
        return str(response.json()['id'])
    
    @staticmethod
    @get_webhook_id.register
    def _(service_type: BBType, *, response: Response) -> str:
        return response.json()['uuid'].strip('{}')


class WebhookDeletionEndpoint:
    @singledispatchmethod
    @staticmethod
    def get_endpoint(service_type: VCSTypes, *, account_name: str,
                     repo_name: str, webhook_id: str) -> str:
        raise NotImplementedError('Unsupported type')
    
    @staticmethod
    @get_endpoint.register
    def _(service_type: GHType, *, account_name: str,
          repo_name: str, webhook_id: str) -> str:
        return '/'.join(
            ('https://api.github.com/repos', account_name, repo_name,
             'hooks', webhook_id)
        )
    
    @staticmethod
    @get_endpoint.register
    def _(service_type: BBType, *, account_name: str,
          repo_name: str, webhook_id: str) -> str:
        return '/'.join(
            ('https://api.bitbucket.org/2.0/repositories', account_name,
             repo_name, 'hooks', webhook_id)
        )


class WebhookDeletionHeaders:
    @singledispatchmethod
    @staticmethod
    def get_headers(service_type: VCSTypes, *, access_token: str) -> Dict[str, str]:
        raise NotImplementedError('Unsupported type')
    
    @staticmethod
    @get_headers.register
    def _(service_type: GHType, *, access_token: str) -> Dict[str, str]:
        return {'Authorization': f'Bearer {access_token}'}
    
    @staticmethod
    @get_headers.register
    def _(service_type: BBType, *, access_token: str) -> Dict[str, str]:
        return {'Authorization': f'Bearer {access_token}'}


class AccessTokenRefreshEndpoint:
    @singledispatchmethod
    @staticmethod
    def get_endpoint(service_type: VCSTypes) -> Union[str, None]:
        raise NotImplementedError('Unsupported type')
    
    @staticmethod
    @get_endpoint.register
    def _(service_type: GHType) -> Union[str, None]:
        return None
    
    @staticmethod
    @get_endpoint.register
    def _(service_type: BBType) -> Union[str, None]:
        return 'https://bitbucket.org/site/oauth2/access_token'


class AccessTokenRefreshPayload:
    @singledispatchmethod
    @staticmethod
    def get_payload(service_type: VCSTypes, *,
                    refresh_token: Union[str, None]) -> Union[Dict[str, str], None]:
        raise NotImplementedError('Unsupported type')
    
    @staticmethod
    @get_payload.register
    def _(service_type: GHType, *,
          refresh_token: Union[str, None] = None) -> Union[Dict[str, str], None]:
        return None
    
    @staticmethod
    @get_payload.register
    def _(service_type: BBType, *,
          refresh_token: Union[str, None]) -> Union[Dict[str, str], None]:
        return {
            'grant_type': 'refresh_token',
            'client_id': settings.VCS_CREDENTIALS['BITBUCKET']['client_id'],
            'client_secret': settings.VCS_CREDENTIALS['BITBUCKET'][
                'client_secret'],
            'refresh_token': refresh_token
        }


class AccessTokenRevokeEndpoint:
    @singledispatchmethod
    @staticmethod
    def get_endpoint(service_type: VCSTypes) -> Union[str, None]:
        raise NotImplementedError('Unsupported type')
    
    @staticmethod
    @get_endpoint.register
    def _(service_type: GHType) -> Union[str, None]:
        return '/'.join(
            ('https://api.github.com/applications',
             settings.VCS_CREDENTIALS['GITHUB']['client_id'], 'grant')
        )
    
    @staticmethod
    @get_endpoint.register
    def _(service_type: BBType) -> Union[str, None]:
        return None


class AccessTokenRevokeHeaders:
    @singledispatchmethod
    @staticmethod
    def get_headers(service_type: VCSTypes) -> Union[Dict[str, str], None]:
        raise NotImplementedError('Unsupported type')
    
    @staticmethod
    @get_headers.register
    def _(service_type: GHType) -> Union[Dict[str, str], None]:
        return {
            'Authorization': 'Basic ' + base64.b64encode(
                bytes(
                    settings.VCS_CREDENTIALS['GITHUB']['client_id']
                    + ':'
                    + settings.VCS_CREDENTIALS['GITHUB']['client_secret'],
                    'utf-8'
                )
            ).decode('utf-8')
        }
    
    @staticmethod
    @get_headers.register
    def _(service_type: BBType) -> Union[Dict[str, str], None]:
        return None


class AccessTokenRevokePayload:
    @singledispatchmethod
    @staticmethod
    def get_payload(service_type: VCSTypes, *,
                    access_token: Union[str, None]) -> Union[str, None]:
        raise NotImplementedError('Unsupported type')
    
    @staticmethod
    @get_payload.register
    def _(service_type: GHType, *,
          access_token: Union[str, None]) -> Union[str, None]:
        return json.dumps({'access_token': access_token})
    
    @staticmethod
    @get_payload.register
    def _(service_type: BBType, *,
          access_token: Union[str, None] = None) -> Union[str, None]:
        return None
