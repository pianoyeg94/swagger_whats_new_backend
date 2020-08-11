from typing import OrderedDict

from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.serializers import Serializer
from rest_framework.fields import Field

from apps.swagger_projects.models import RemoteVCSAccount


def validate_remote_vcs_account_temp_token(data: dict,
                                           serializer: Serializer) -> dict:
    """
    Validate temporary OAuth VCS token
    and deligate OAuth access token processing
    to underlying model method implementation.
    """
    remote_vcs_account = RemoteVCSAccount(
        remote_vcs_service=data['remote_vcs_service'],
        account_type=data['account_type'],
        account_name=data['account_name']
    )
    try:
        remote_vcs_account.set_and_validate_access_token(data['temporary_token'])
        data.clear()
        data['remote_vcs_account'] = remote_vcs_account
    except ValidationError as e:
        raise serializers.ValidationError(e.message)

    return data


class RemoteVCSAccountRegisteredValidator:
    requires_context = True

    def __call__(self, value: OrderedDict, serializer_field: Field) -> None:
        """Validate whether a VCS account is registered in "our" system or not"""
        serializer = serializer_field.parent
        company_id = serializer.context['request'].user.company_id
        try:
            serializer.context['remote_vcs_account'] = RemoteVCSAccount.objects.get(
                account_name=value['account_name'],
                remote_vcs_service=value['remote_vcs_service'],
                company_id=company_id
            )
        except RemoteVCSAccount.DoesNotExist:
            raise serializers.ValidationError(
                'Provided VCS account has not been created yet.')
