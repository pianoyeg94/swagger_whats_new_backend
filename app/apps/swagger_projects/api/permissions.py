from rest_framework import permissions

from apps.swagger_projects.models import SwaggerFileChange


class IsCommentOwnerOrReadOnly(permissions.BasePermission):
    
    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.swagger_file_change_comments.filter(id=obj.id).exists()
        )


class IsCompanyMember(permissions.BasePermission):
    
    def has_permission(self, request, view):
        swagger_file_change_id = view.kwargs.get('swagger_file_change_id')
        return request.user.company_id == SwaggerFileChange.objects.get(
            id=swagger_file_change_id).swagger_project.company.id
