from rest_framework import serializers

from shared.validators import UniqueWithinCompanyValidator
from apps.accounts.api.validators import PermissionSetValidator
from apps.accounts.models import Company, CompanyInvitation
from .company import CompanySerializer
from .user import UserWithTokenSerializer


class CompanyAccountSerializer(serializers.Serializer):
    company = CompanySerializer()
    user = UserWithTokenSerializer()

    def create(self, validated_data: dict) -> dict:
        company_membership = validated_data['user'].pop('company_membership')
        validated_data['user'].pop('password_confirm')

        company, user = Company.objects.create_company_account(
            company_data=validated_data['company'],
            user_data=validated_data['user'],
            membership_data=company_membership
        )

        return {'company': company, 'user': user}


class CompanyInvitationSerializer(serializers.ModelSerializer):
    desired_company_permissions = serializers.IntegerField(
        validators=[PermissionSetValidator()]
    )

    class Meta:
        model = CompanyInvitation
        fields = ('id', 'email', 'desired_company_permissions')
        validators = [
            UniqueWithinCompanyValidator(
                queryset=CompanyInvitation.objects.all(),
                fields=['email']
            )
        ]

    def create(self, validated_data: dict) -> CompanyInvitation:
        user = self.context['request'].user

        invitation = CompanyInvitation.objects.create(
            **validated_data,
            company=user.company
        )

        return invitation
