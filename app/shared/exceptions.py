from typing import Union

from django.http import Http404
from django.core.exceptions import PermissionDenied
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler
from rest_framework.response import Response

DefaultExceptionTypes = Union[APIException, Http404, PermissionDenied]


class APIExceptionWithCode200(APIException):
    """Used to hide some internal implementations"""
    default_detail = {}
    status_code = 200


def custom_exception_handler(exc: DefaultExceptionTypes, context: dict) -> Response:
    response = exception_handler(exc, context)
    
    if response is not None and response.data != {}:
        response.data = {'message': response.data}
    
    return response
