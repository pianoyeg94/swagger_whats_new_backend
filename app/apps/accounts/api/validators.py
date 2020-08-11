from typing import OrderedDict

from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.serializers import Serializer
from rest_framework.fields import Field

from apps.accounts.models import CompanyInvitation, CompanyMembership


class CompanyInvitationTokenValidator:
    requires_context = True
    
    def __call__(self, attrs: OrderedDict, serializer: Serializer) -> None:
        """
        Find company invitation by invitation token,
        raise validation error if invitation wasn't found.
        """
        invitation_token = serializer.context['invitation_token']
        try:
            company_invitation = \
                CompanyInvitation.objects.validate_get_by_invitation_token(
                    invitation_token)
            serializer.context['company_invitation'] = company_invitation
        except ValidationError as e:
            raise serializers.ValidationError(e.message)


class PasswordValidator:
    requires_context = True
    
    def __call__(self, value: str, serializer_field: Field) -> None:
        """
        Get user instance and validate current password
        via django's "check_password" default user model method.
        """
        instance = serializer_field.parent.instance
        verification_success = instance.check_password(value)
        if not verification_success:
            raise serializers.ValidationError(
                'Please provide a valid current password.')


class PermissionSetValidator:
    
    def __call__(self, value: int) -> None:
        """
        Validate that a given set of permissions
        matches existing permission permutations (sum of permutations).
        """
        try:
            CompanyMembership.objects.validate_permissions_set(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.message)
