import logging
from typing import Union, Iterable

from django.db.models import QuerySet
from django.http import Http404
from django.contrib.auth import get_user_model
from rest_framework import generics
from rest_framework import mixins
from rest_framework.request import Request
from rest_framework.views import APIView, Response
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated

from utils.functions import convert_enum_to_dict
from shared.permissions import IsCompanyOwnerOrReadOnly
from shared.pagination import StandardResultsSetPagination
from apps.accounts.models import CompanyMembership, UserProfile
from apps.accounts.api.filter_sets import UserFilter
from apps.accounts.api.serializers import (
    UpdateMeSerializer,
    UserProfilePhotoSerializer,
    UserProfileSerializer,
    CompanyMembershipPermissionsSerializer,
    CompanyMembershipPermissionsListSerializer,
    UserWithCompanyMembershipAndProfileSerializer
)

logger = logging.getLogger(__name__)
User = get_user_model()


class MeUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UpdateMeSerializer
    queryset = User.objects.all()
    http_method_names = ('put', 'patch', 'delete', 'head', 'options')
    permission_classes = (IsAuthenticated,)
    
    def get_object(self) -> User:
        return self.request.user


class UserProfilePhotoUploadDeleteAPIView(mixins.UpdateModelMixin,
                                          mixins.DestroyModelMixin,
                                          generics.GenericAPIView):
    serializer_class = UserProfilePhotoSerializer
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser,)
    
    def get_object(self) -> UserProfile:
        return self.request.user.profile
    
    def perform_destroy(self, instance: UserProfile) -> None:
        instance.profile_photo.delete()
    
    def delete(self, request: Request, *args, **kwargs) -> Response:
        return self.destroy(request, *args, **kwargs)
    
    def put(self, request: Request, *args, **kwargs) -> Response:
        return self.update(request, *args, **kwargs)


class UserProfileRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticated,)
    
    def get_object(self) -> UserProfile:
        return self.request.user.profile


class UserListAPIView(generics.ListAPIView):
    serializer_class = UserWithCompanyMembershipAndProfileSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = StandardResultsSetPagination
    filterset_class = UserFilter
    
    def get_queryset(self) -> Union[QuerySet, Iterable[User]]:
        return User.objects.filter(
            companies__id=self.request.user.company_id).order_by('created_at')


class UserRetrieveDestroyAPIView(generics.RetrieveDestroyAPIView):
    serializer_class = UserWithCompanyMembershipAndProfileSerializer
    permission_classes = (IsAuthenticated, IsCompanyOwnerOrReadOnly)

    def get_queryset(self) -> Union[QuerySet, Iterable[User]]:
        return User.objects.filter(
            companies__id=self.request.user.company_id).order_by('created_at')


class UsersCompanyMembershipPermissionsUpdateAPIView(generics.UpdateAPIView):
    serializer_class = CompanyMembershipPermissionsSerializer
    permission_classes = (IsAuthenticated, IsCompanyOwnerOrReadOnly)
    
    def get_queryset(self) -> Union[QuerySet, Iterable[CompanyMembership]]:
        return CompanyMembership.objects.filter(
            company__id=self.request.user.company_id)
    
    def get_object(self) -> CompanyMembership:
        user_id = User.objects.values_list('id', flat=True).filter(
            id=self.kwargs['pk']).first()
        
        try:
            company_membership = CompanyMembership.objects.get(user_id=user_id)
        except CompanyMembership.DoesNotExist:
            raise Http404
        
        return company_membership


class CompanyMembershipPermissionsListAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    
    def get(self, request: Request) -> Response:
        """
        Convert app's company membership permissions enum into a dictionary
        and return it with the response body.
        """
        company_membership_permissions_dict = convert_enum_to_dict(
            enum=CompanyMembership.PERMISSIONS_ENUM,
            lowercase_keys=True
        )
        data = CompanyMembershipPermissionsListSerializer(
            company_membership_permissions_dict).data
        
        return Response(data=data)
