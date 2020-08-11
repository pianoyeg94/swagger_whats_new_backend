from rest_framework import serializers

from shared.validators import UniqueWithinCompanyValidator
from apps.swagger_projects.models import RemoteVCSAccount
from apps.swagger_projects.api.validators import \
    validate_remote_vcs_account_temp_token


class PartialRemoteVCSAccountSerializer(serializers.ModelSerializer):
    remote_vcs_service = serializers.ChoiceField(
        choices=RemoteVCSAccount.REMOTE_VCS_SERVICE_CHOICES
    )
    account_name = serializers.CharField()

    class Meta:
        model = RemoteVCSAccount
        fields = ('remote_vcs_service', 'account_name')


class RemoteVCSAccountSerializer(serializers.ModelSerializer):
    remote_vcs_service = serializers.ChoiceField(
        choices=RemoteVCSAccount.REMOTE_VCS_SERVICE_CHOICES
    )
    account_type = serializers.ChoiceField(
        choices=RemoteVCSAccount.ACCOUNT_TYPE_CHOICES
    )
    account_name = serializers.CharField()
    temporary_token = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = RemoteVCSAccount
        fields = ('id', 'account_name', 'remote_vcs_service', 'account_type',
                  'temporary_token', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')
        validators = [
            UniqueWithinCompanyValidator(
                queryset=RemoteVCSAccount.objects.all(),
                fields=['remote_vcs_service', 'account_name']
            )
        ]

    def validate(self, data: dict) -> dict:
        return validate_remote_vcs_account_temp_token(data, self)

    def create(self, validated_data: dict) -> RemoteVCSAccount:
        company_id = self.context['request'].user.company_id
        remote_vcs_account = validated_data['remote_vcs_account']
        remote_vcs_account.company_id = company_id
        remote_vcs_account.save()

        return remote_vcs_account
