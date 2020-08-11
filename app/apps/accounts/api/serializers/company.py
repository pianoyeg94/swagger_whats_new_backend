from rest_framework import serializers

from apps.accounts.models import Company


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ('id', 'company_name', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')
