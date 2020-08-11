from typing import Type, Union

from .utils import VCSAuthUtility, VCSWebhookUtiltity


class BaseVCSUtilFactory:
    def __init__(self):
        self._utils = {}
    
    def register_util(self, remote_vcs_service: str,
                      util: Type[Union[VCSAuthUtility, VCSWebhookUtiltity]]) -> None:
        self._utils[remote_vcs_service] = util(remote_vcs_service)
    
    def get_util(self, remote_vcs_service: str) -> None:
        util = self._utils.get(remote_vcs_service)
        if not util:
            raise ValueError(remote_vcs_service)
        return util


class VCSAuthUtilFactory(BaseVCSUtilFactory):
    """
    Factory that exposes concrete implementations of VCSAuthUtility methods
    depending on provided VCS service type
    """


class VCSWebhookUtilFactory(BaseVCSUtilFactory):
    """
    Factory that exposes concrete implementations of VCSWebhookUtility methods
    depending on provided VCS service type
    """


vcs_auth_util_factory = VCSAuthUtilFactory()
vcs_webhook_util_factory = VCSWebhookUtilFactory()

vcs_auth_util_factory.register_util('GH', VCSAuthUtility)
vcs_auth_util_factory.register_util('BB', VCSAuthUtility)

vcs_webhook_util_factory.register_util('GH', VCSWebhookUtiltity)
vcs_webhook_util_factory.register_util('BB', VCSWebhookUtiltity)
