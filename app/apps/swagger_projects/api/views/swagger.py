from typing import Union, Iterable, Type

from django.db.models import QuerySet
from django.http import Http404
from rest_framework import generics
from rest_framework import mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.permissions import IsAuthenticated

from shared.pagination import StandardResultsSetPagination
from apps.swagger_projects.api.permissions import IsCommentOwnerOrReadOnly
from apps.swagger_projects.signals import trigger_webhook_callback_signal
from apps.swagger_projects.api.filter_sets import SwaggerProjectFilter
from shared.permissions import (
    IsCompanyOwnerOrHasObjectPermissionOrReadOnly,
    check_object_permissions
)
from apps.swagger_projects.models import (
    SwaggerProject,
    SwaggerFileChange,
    SwaggerFileChangeComment,
)
from apps.swagger_projects.api.serializers import (
    SwaggerProjectWithVCSSerializer,
    SwaggerProjectWithoutVCSSerializer,
    SwaggerFileChangesSerializer,
    SwaggerFileChangeCommentSerializer,
)

SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')


@check_object_permissions(obj=SwaggerProject, methods=['create'])
class SwaggerProjectListCreateAPIView(generics.ListCreateAPIView):
    pagination_class = StandardResultsSetPagination
    filterset_class = SwaggerProjectFilter
    permission_classes = (
        IsAuthenticated,
        IsCompanyOwnerOrHasObjectPermissionOrReadOnly
    )
    
    def get_queryset(self) -> Union[QuerySet, Iterable[SwaggerProject]]:
        queryset = SwaggerProject.objects.filter(
            company_id=self.request.user.company_id).order_by('created_at')
        
        return queryset
    
    def get_serializer_class(self) -> Type[Union[SwaggerProjectWithoutVCSSerializer,
                                                 SwaggerProjectWithVCSSerializer]]:
        """
        Returns different serializer classes based on the request context,
        this serializer is then used by the view.
        
        Returns SwaggerProjectWithoutVCSSerializer when:
        1) A GET, OPTIONS or HEAD request was submitted.
        2) "use_vcs" field was not provided within the POST request body.
        3) "use_vcs" field was set to false within the POST request body.
       
        Returns SwaggerProjectWithVCSSerializer when:
        1) "use_vcs" field was set to true within the POST request body
        """
        if self.request.method in SAFE_METHODS:
            return SwaggerProjectWithoutVCSSerializer
        else:
            try:
                return (
                    SwaggerProjectWithVCSSerializer
                    if self.request.data['use_vcs']
                    else SwaggerProjectWithoutVCSSerializer
                )
            except KeyError:
                return SwaggerProjectWithoutVCSSerializer


class SwaggerProjectRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SwaggerProjectWithoutVCSSerializer
    permission_classes = (
        IsAuthenticated,
        IsCompanyOwnerOrHasObjectPermissionOrReadOnly,
    )
    
    def get_queryset(self) -> Union[QuerySet, Iterable[SwaggerProject]]:
        queryset = SwaggerProject.objects.filter(
            company_id=self.request.user.company_id)
        
        return queryset


class SwaggerProjectWebhookCallbackAPIView(APIView):
    
    def post(self, request: Request) -> Response:
        """
        Offloads the actual webhook request processing to a custom signal handler
        which in turn offloads it to a separate thread.
        
        Immediately returns a 200 status code response.
        """
        trigger_webhook_callback_signal.send(
            sender=SwaggerProjectWebhookCallbackAPIView,
            remote_vcs_service_header=request.headers['User-Agent'],
            request_data=request.data,
        )
        return Response()


class SwaggerFileChangesListAPIView(generics.ListAPIView):
    serializer_class = SwaggerFileChangesSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_queryset(self) -> Union[QuerySet, Iterable[SwaggerFileChange]]:
        swagger_project_id = self.kwargs.get('swagger_project_id')
        # find swagger file changes belonging to user's company
        # and requested swagger project,
        # exclude swagger file changes
        # not yet processed by the swagger file changes worker
        queryset = (
            SwaggerFileChange.objects.filter(
                swagger_project_id=swagger_project_id,
                swagger_project__company_id=self.request.user.company_id,
            )
            .exclude(swagger_file_changes={})
            .order_by('changes_added_at')
        )
        
        return queryset


class SwaggerFileChangeRetrieveAPIView(generics.RetrieveAPIView):
    serializer_class = SwaggerFileChangesSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_queryset(self) -> Union[QuerySet, Iterable[SwaggerFileChange]]:
        swagger_project_id = self.kwargs.get('swagger_project_id')
        # find swagger file changes belonging to user's company
        # and requested swagger project,
        # exclude swagger file changes
        # not yet processed by the swagger file changes worker
        queryset = (
            SwaggerFileChange.objects.filter(
                swagger_project_id=swagger_project_id,
                swagger_project__company_id=self.request.user.company_id,
            )
            .exclude(swagger_file_changes={})
            .order_by('changes_added_at')
        )
        
        return queryset


class SwaggerFileChangeCommentCreateAPIView(generics.CreateAPIView):
    serializer_class = SwaggerFileChangeCommentSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_serializer_context(self) -> dict:
        """
        Raises a 404 error code if a user tries to:
        1) Comment on a non-existing swagger file change.
        2) Comment on a swagger file change from another company.
        3) Comment on a swagger file change
           which provides commit details functionality but wasn't yet processed
           by the swagger file changes worker.
        
        Otherwise it stores the swagger file change id in a context dictionary,
        which will later be used by the serializer.
        """
        context = super().get_serializer_context()
        try:
            swagger_file_change = SwaggerFileChange.objects.get(
                id=self.kwargs.get('swagger_file_change_id'))
            swagger_file_change_company_id = \
                swagger_file_change.swagger_project.company.id
        except SwaggerFileChange.DoesNotExist:
            raise Http404
        
        if (
            self.request.user.company_id != swagger_file_change_company_id
            or not swagger_file_change.swagger_file_changes
        ):
            raise Http404
        
        context['swagger_file_change_id'] = swagger_file_change.id
        
        return context


class SwaggerFileChangeCommentUpdateDestroyAPIView(mixins.UpdateModelMixin,
                                                   mixins.DestroyModelMixin,
                                                   generics.GenericAPIView):
    serializer_class = SwaggerFileChangeCommentSerializer
    permission_classes = (IsAuthenticated, IsCommentOwnerOrReadOnly)
    
    def get_queryset(self) -> Union[QuerySet, Iterable[SwaggerFileChangeComment]]:
        swagger_file_change_id = self.kwargs.get('swagger_file_change_id')
        queryset = SwaggerFileChangeComment.objects.filter(
            swagger_file_change_id=swagger_file_change_id)
        
        return queryset
    
    def delete(self, request: Request, *args, **kwargs) -> Response:
        return self.destroy(request, *args, **kwargs)
    
    def put(self, request: Request, *args, **kwargs) -> Response:
        return self.update(request, *args, **kwargs)
