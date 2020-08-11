from requests.adapters import HTTPAdapter

from django.conf import settings

DEFAULT_TIMEOUT = settings.REQUESTS_DEFAULT_TIMEOUT_IN_SECONDS


class CustomHTTPAdapter(HTTPAdapter):
    """
    Inherits from HTTPAdapter to provide default request timeout configuration
    """
    
    def __init__(self, *args, **kwargs):
        self.timeout = DEFAULT_TIMEOUT
        if 'timeout' in kwargs:
            self.timeout = kwargs['timeout']
            del kwargs['timeout']
        super().__init__(*args, **kwargs)
    
    def send(self, request, **kwargs):
        timeout = kwargs.get('timeout')
        if timeout is None:
            kwargs['timeout'] = self.timeout
        return super().send(request, **kwargs)
