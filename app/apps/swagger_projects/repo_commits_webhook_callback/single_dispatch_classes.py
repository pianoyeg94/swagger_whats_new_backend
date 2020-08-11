from functools import singledispatchmethod
from typing import Dict, Union, List

from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist

from apps.swagger_projects.models import RemoteVCSAccount, SwaggerProject

APP = apps.get_app_config('swagger_projects')
VCS_TYPES = APP.vcs_types
GHType = VCS_TYPES.GH.value
BBType = VCS_TYPES.BB.value
VCSTypes = Union[GHType, BBType]

"""
Container classes that use single dispatch methods
to provide concrete implementations of VCS repository webhook callback parsers.

Concrete implementations depend on specified VCS service types
(currently Github and Bitbucket integrations are supported)
"""


class RemoteVcsAccountIdFactory:
    @singledispatchmethod
    @staticmethod
    def get_instance_id(service_type: VCSTypes, *, data: dict) -> int:
        raise NotImplementedError('Unsupported type')
    
    @staticmethod
    @get_instance_id.register
    def _(service_type: GHType, *, data: dict) -> int:
        try:
            obj_id = RemoteVCSAccount.objects.values_list('id', flat=True).filter(
                account_name=data['repository']['owner']['name'],
                remote_vcs_service='GH'
            ).first()
        except KeyError:
            raise ObjectDoesNotExist()
        
        if not obj_id:
            raise ObjectDoesNotExist()
        
        return obj_id
    
    @staticmethod
    @get_instance_id.register
    def _(service_type: BBType, *, data: dict) -> int:
        try:
            obj_id = RemoteVCSAccount.objects.values_list('id', flat=True).filter(
                account_name=data['repository']['full_name'].split('/')[0],
                remote_vcs_service='BB'
            ).first()
        except KeyError:
            raise ObjectDoesNotExist()
        
        if not obj_id:
            raise ObjectDoesNotExist()
        
        return obj_id


class SwaggerProjectInstanceIdFactory:
    @singledispatchmethod
    @staticmethod
    def get_instance_id(service_type: VCSTypes, *,
                        data: dict, remote_vcs_account_id: int) -> int:
        raise NotImplementedError('Unsupported type')
    
    @staticmethod
    @get_instance_id.register
    def _(service_type: GHType, *, data: dict, remote_vcs_account_id: int) -> int:
        try:
            obj_id = SwaggerProject.objects.values_list('id', flat=True).filter(
                remote_vcs_account_id=remote_vcs_account_id,
                remote_repo_name=data['repository']['name'],
                remote_repo_branch=data['ref'].split('/')[-1]
            ).first()
        except KeyError:
            raise ObjectDoesNotExist()
        
        if not obj_id:
            raise ObjectDoesNotExist()
        
        return obj_id
    
    @staticmethod
    @get_instance_id.register
    def _(service_type: BBType, *, data: dict, remote_vcs_account_id: int) -> int:
        try:
            obj_id = SwaggerProject.objects.values_list('id', flat=True).filter(
                remote_vcs_account_id=remote_vcs_account_id,
                remote_repo_name=data['repository']['name'],
                remote_repo_branch=data['push']['changes'][0]['new']['name'],
            ).first()
        except KeyError:
            raise ObjectDoesNotExist()
        
        if not obj_id:
            raise ObjectDoesNotExist()
        
        return obj_id


class RelatedCommitDetailsParser:
    @singledispatchmethod
    @staticmethod
    def get_related_commit_details(service_type: VCSTypes, *, data: dict,
                                   timestamp: str) -> Dict[str, Union[str, List[str]]]:
        raise NotImplementedError('Unsupported type')
    
    @staticmethod
    @get_related_commit_details.register
    def _(service_type: GHType, *, data: dict,
          timestamp: str) -> Dict[str, Union[str, List[str]]]:
        return {
            'pushed_by': data['pusher']['name'],
            'timestamp': timestamp,
            'commit_urls': [commit['url'] for commit in data['commits']],
        }
    
    @staticmethod
    @get_related_commit_details.register
    def _(service_type: BBType, *, data: dict,
          timestamp: str) -> Dict[str, Union[str, List[str]]]:
        return {
            'pushed_by': data['actor']['display_name'],
            'timestamp': timestamp,
            'commit_urls': [
                commit['links']['html']['href']
                for commit in data['push']['changes'][0]['commits']
            ],
        }
