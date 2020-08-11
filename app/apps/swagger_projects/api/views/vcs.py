from typing import Union, Iterable

from django.db.models import QuerySet
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from shared.pagination import StandardResultsSetPagination
from apps.swagger_projects.models import RemoteVCSAccount
from apps.swagger_projects.api.serializers import RemoteVCSAccountSerializer
from apps.swagger_projects.api.filter_sets import RemoteVCSAccountFilter
from shared.permissions import (
    IsCompanyOwnerOrHasObjectPermissionOrReadOnly,
    check_object_permissions
)


@check_object_permissions(obj=RemoteVCSAccount, methods=['create'])
class RemoteVCSAccountListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = RemoteVCSAccountSerializer
    filterset_class = RemoteVCSAccountFilter
    pagination_class = StandardResultsSetPagination
    permission_classes = (
        IsAuthenticated,
        IsCompanyOwnerOrHasObjectPermissionOrReadOnly,
    )
    
    def get_queryset(self) -> Union[QuerySet, Iterable[RemoteVCSAccount]]:
        queryset = RemoteVCSAccount.objects.filter(
            company_id=self.request.user.company_id).order_by('created_at')
        
        return queryset


class RemoteVCSAccountRetrieveDestroyAPIView(generics.RetrieveDestroyAPIView):
    serializer_class = RemoteVCSAccountSerializer
    permission_classes = (
        IsAuthenticated,
        IsCompanyOwnerOrHasObjectPermissionOrReadOnly,
    )
    
    def get_queryset(self) -> Union[QuerySet, Iterable[RemoteVCSAccount]]:
        queryset = RemoteVCSAccount.objects.filter(
            company_id=self.request.user.company_id)
        
        return queryset
