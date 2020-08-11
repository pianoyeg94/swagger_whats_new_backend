import enum
import requests
from functools import partial
from requests.packages.urllib3.util.retry import Retry
from typing import Union

from django.apps import AppConfig

from shared.custom_http_adapter import CustomHTTPAdapter
from utils.metaclasses import Singleton


class VcsTypes(enum.Enum):
    GH = Singleton('GH', (object,), {})
    BB = Singleton('BB', (object,), {})


def get_remote_vcs_service_type(vcs_types_enum: VcsTypes,
                                str_representation_of_type: str) -> Union[VcsTypes.GH.value,
                                                                          VcsTypes.BB.value]:
    try:
        return vcs_types_enum[str_representation_of_type].value()
    except KeyError:
        raise NotImplementedError('Unsupported type')


class SwaggerProjectsConfig(AppConfig):
    name = 'apps.swagger_projects'
    
    def __init__(self, app_name, app_module):
        super().__init__(app_name, app_module)
        self.vcs_types = VcsTypes  # VCS types enum
        self.get_vcs_service_type = partial(
            get_remote_vcs_service_type,
            self.vcs_types
        )
        
        # prepare custom "requests" adapter
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=['HEAD', 'GET', 'POST', 'PUT',
                              'DELETE', 'OPTIONS', 'TRACE']
        )
        adapter = CustomHTTPAdapter(max_retries=retry_strategy)
        self.http = requests.Session()
        self.http.mount('https://', adapter)
        self.http.mount('http://', adapter)
    
    def ready(self) -> None:
        import apps.swagger_projects.signals
