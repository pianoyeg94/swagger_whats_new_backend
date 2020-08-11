from django.core.exceptions import ValidationError
from rest_framework import serializers

from .vcs import PartialRemoteVCSAccountSerializer
from apps.swagger_projects.api.validators import \
    RemoteVCSAccountRegisteredValidator
from apps.accounts.api.serializers import \
    UserWithCompanyMembershipAndProfileSerializer
from shared.validators import (
    UniqueWithinCompanyValidator,
    UniqueTogetherWithNestedSerializerValidator,
)
from apps.swagger_projects.models import (
    SwaggerProject,
    RemoteVCSAccount,
    SwaggerFileChange,
    SwaggerFileChangeComment,
)


class SwaggerProjectWithoutVCSSerializer(serializers.ModelSerializer):
    """
    This serializer is used for swagger projects
    that are not integrated with a remote VCS account
    """
    
    remote_vcs_account = PartialRemoteVCSAccountSerializer(read_only=True)
    project_owner_id = serializers.PrimaryKeyRelatedField(
        source='project_owner',
        read_only=True
    )
    
    class Meta:
        model = SwaggerProject
        fields = ('id', 'project_name', 'swagger_file_url', 'project_owner_id',
                  'use_vcs', 'remote_vcs_account', 'remote_repo_name',
                  'remote_repo_branch', 'created_at', 'updated_at')
        read_only_fields = ('id', 'remote_repo_name', 'remote_repo_branch',
                            'created_at', 'updated_at')
        validators = [
            UniqueWithinCompanyValidator(
                queryset=SwaggerProject.objects.all(),
                fields=['project_name']
            )
        ]
    
    def create(self, validated_data: dict) -> SwaggerProject:
        request = self.context['request']
        swagger_project = SwaggerProject.objects.create(
            **validated_data,
            company_id=request.user.company_id,
            project_owner=request.user
        )
        
        return swagger_project
    
    def update(self, instance: SwaggerProject, validated_data: dict) -> SwaggerProject:
        # "swagger_file_url" and "use_vcs" values cannot be modified
        validated_data.pop('swagger_file_url')
        validated_data.pop('use_vcs')
        return super().update(instance, validated_data)


class SwaggerProjectWithVCSSerializer(serializers.ModelSerializer):
    """
    This serializer is used for swagger projects
    that are integrated with a remote VCS account
    """
    
    remote_vcs_account = PartialRemoteVCSAccountSerializer(
        validators=[RemoteVCSAccountRegisteredValidator()]
    )
    project_owner_id = serializers.PrimaryKeyRelatedField(
        source='project_owner',
        read_only=True
    )
    
    class Meta:
        model = SwaggerProject
        fields = ('id', 'project_name', 'swagger_file_url', 'project_owner_id',
                  'use_vcs', 'remote_vcs_account', 'remote_repo_name',
                  'remote_repo_branch', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')
        validators = [
            UniqueWithinCompanyValidator(
                queryset=SwaggerProject.objects.all(),
                fields=['project_name']
            ),
            UniqueTogetherWithNestedSerializerValidator(
                queryset=SwaggerProject.objects.all(),
                fields=['remote_repo_name', 'remote_repo_branch'],
                nested_serializer_field='remote_vcs_account',
                nested_serializer_model=RemoteVCSAccount
            ),
        ]
    
    def create(self, validated_data: dict) -> SwaggerProject:
        request = self.context['request']
        # set by RemoteVCSAccountRegisteredValidator field validator
        remote_vcs_account = self.context['remote_vcs_account']
        validated_data.pop('remote_vcs_account')
        
        swagger_project = SwaggerProject(
            **validated_data,
            company_id=request.user.company_id,
            project_owner=request.user,
            remote_vcs_account=remote_vcs_account
        )
        
        try:
            swagger_project.set_webhook_id()
        except ValidationError as e:
            raise serializers.ValidationError(e.message)
        
        swagger_project.save()
        
        return swagger_project
    
    def update(self, instance: SwaggerProject, validated_data: dict) -> SwaggerProject:
        # all these fields cannot be modified
        validated_data.pop('swagger_file_url')
        validated_data.pop('use_vcs')
        validated_data.pop('remote_vcs_account')
        validated_data.pop('remote_repo_name')
        validated_data.pop('remote_repo_branch')
        return super().update(instance, validated_data)


class SwaggerFileChangeCommentSerializer(serializers.ModelSerializer):
    comment_author = UserWithCompanyMembershipAndProfileSerializer(read_only=True)
    
    class Meta:
        model = SwaggerFileChangeComment
        fields = ('id', 'comment_text', 'comment_author',
                  'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at', 'comment_author')
    
    def create(self, validated_data: dict) -> SwaggerFileChangeComment:
        swagger_file_change_comment = SwaggerFileChangeComment.objects.create(
            **validated_data,
            comment_author=self.context['request'].user,
            swagger_file_change_id=self.context['swagger_file_change_id']
        )
        
        return swagger_file_change_comment


class SwaggerFileChangesSerializer(serializers.ModelSerializer):
    comments = SwaggerFileChangeCommentSerializer(many=True)
    
    class Meta:
        model = SwaggerFileChange
        fields = ('id', 'related_commit_details', 'swagger_file_changes',
                  'comments', 'changes_added_at')
        read_only_fields = ('id', 'related_commit_details', 'comments',
                            'swagger_file_changes', 'changes_added_at')
