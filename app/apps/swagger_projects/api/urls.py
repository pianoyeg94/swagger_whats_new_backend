from django.urls import path

from apps.swagger_projects.api.views import (
    # remote VCS account resource views
    RemoteVCSAccountListCreateAPIView,
    RemoteVCSAccountRetrieveDestroyAPIView,
    
    # swagger project resource views
    SwaggerProjectListCreateAPIView,
    SwaggerProjectRetrieveUpdateDestroyAPIView,
    SwaggerProjectWebhookCallbackAPIView,
    SwaggerFileChangesListAPIView,
    SwaggerFileChangeRetrieveAPIView,

    # swagger file changes resource views
    SwaggerFileChangeCommentCreateAPIView,
    SwaggerFileChangeCommentUpdateDestroyAPIView,
    
    # utility resource views
    CheckUniqueRepoBranchAPIView,
    CheckUniqueSwaggerProjectNameAPIView,
    CheckUniqueVCSAccountAPIView,
)


remote_vcs_account_related_resources = [
    path(
        'vcs-accounts/',
        RemoteVCSAccountListCreateAPIView.as_view(),
        name='vcs_accounts_list_create',
    ),
    path(
        'vcs-accounts/<int:pk>/',
        RemoteVCSAccountRetrieveDestroyAPIView.as_view(),
        name='vcs_account_retrieve_destroy',
    ),
]

swagger_project_related_resources = [
    path(
        'swagger-projects/',
        SwaggerProjectListCreateAPIView.as_view(),
        name='swagger_projects_list_create',
    ),
    path(
        'swagger-projects/<int:pk>/',
        SwaggerProjectRetrieveUpdateDestroyAPIView.as_view(),
        name='swagger_projects_retrieve_update_destroy',
    ),
    path(
        'swagger-projects/webhook-callback/',
        SwaggerProjectWebhookCallbackAPIView.as_view(),
        name='swagger_projects_webhook_callback',
    ),
    path(
        'swagger-projects/<int:swagger_project_id>/swagger-file-changes/',
        SwaggerFileChangesListAPIView.as_view(),
        name='swagger_project_swagger_file_changes_list',
    ),
    path(
        'swagger-projects/<int:swagger_project_id>/swagger-file-changes/<int:pk>/',
        SwaggerFileChangeRetrieveAPIView.as_view(),
        name='swagger-projects-swagger-file-changes-detail',
    ),
]

swagger_file_changes_related_resources = [
    path(
        'swagger-file-changes/<int:swagger_file_change_id>/comments/',
        SwaggerFileChangeCommentCreateAPIView.as_view(),
        name='swagger-file-changes-comment-create',
    ),
    path(
        'swagger-file-changes/<int:swagger_file_change_id>/comments/<int:pk>/',
        SwaggerFileChangeCommentUpdateDestroyAPIView.as_view(),
        name='swagger-file-changes-comment-update-delete',
    ),
]

utility_related_resources = [
    path(
        'utility/vcs-account-exists/',
        CheckUniqueVCSAccountAPIView.as_view(),
        name='utility-vcs-account-exists',
    ),
    path(
        'utility/swagger-project-exists/',
        CheckUniqueSwaggerProjectNameAPIView.as_view(),
        name='utility-swagger-project-exists',
    ),
    path(
        'utility/remote-repo-branch-exists/',
        CheckUniqueRepoBranchAPIView.as_view(),
        name='utility-remote-repo-branch-exists',
    ),
]

urlpatterns = [
    *remote_vcs_account_related_resources,
    *swagger_project_related_resources,
    *swagger_file_changes_related_resources,
    *utility_related_resources,
]