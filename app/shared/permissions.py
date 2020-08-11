from functools import singledispatchmethod, wraps
from inspect import isroutine
from typing import Union

from rest_framework.views import View
from rest_framework import permissions
from rest_framework.request import Request

from apps.accounts.models import CompanyInvitation, CompanyMembership
from apps.swagger_projects.models import RemoteVCSAccount, SwaggerProject

UnionModelType = Union[CompanyInvitation, RemoteVCSAccount, SwaggerProject]


class CheckObjectPermissionsClassDecorator:
    """
    Class decorator that decorates specified instance methods (__init__ argument)
    with "permissions_decorator".
    
    "permissions_decorator" calles <View>.check_object_permissions() with provided
    model instance (__init__ argument) before the original method is called.
    """
    
    def __init__(self, obj, methods):
        self.obj = obj
        self.methods = methods
    
    def __call__(self, cls):
        for method_name in self.methods:
            attr = getattr(cls, method_name, None)
            # ignore class and static method descriptors,
            # as well as classes and callable instances of classes
            if attr is not None and callable(attr) and isroutine(attr):
                setattr(cls, method_name, self.permissions_decorator(attr))
                
        return cls
    
    def permissions_decorator(self, fn):
        @wraps(fn)
        def wrapper(view, *args, **kwargs):
            view.check_object_permissions(view.request, self.obj())
            return fn(view, *args, **kwargs)
        
        return wrapper


check_object_permissions = CheckObjectPermissionsClassDecorator


class CompanyMembershipPermissionsMap:
    """
    "get_permission_for_obj" returns different company membership permissions
    depending on provided model instance
    """
    
    _COMPANY_MEMBERSHIP_PERMISSIONS = CompanyMembership.PERMISSIONS_ENUM
    
    @singledispatchmethod
    @classmethod
    def get_permission_for_obj(cls, arg: UnionModelType) -> int:
        raise NotImplementedError('Unsupported type')
    
    @get_permission_for_obj.register(CompanyInvitation)
    @classmethod
    def _(cls, arg: CompanyInvitation) -> int:
        return cls._COMPANY_MEMBERSHIP_PERMISSIONS.INVITE_NEW_USERS.value
    
    @get_permission_for_obj.register(RemoteVCSAccount)
    @classmethod
    def _(cls, arg: RemoteVCSAccount) -> int:
        return cls._COMPANY_MEMBERSHIP_PERMISSIONS.REGISTER_VCS_ACCOUNTS.value
    
    @get_permission_for_obj.register(SwaggerProject)
    @classmethod
    def _(cls, arg: SwaggerProject) -> int:
        return cls._COMPANY_MEMBERSHIP_PERMISSIONS.CREATE_SWAGGER_PROJECTS.value


class IsCompanyOwnerOrHasObjectPermissionOrReadOnly(permissions.BasePermission):
    
    def has_object_permission(self, request: Request,
                              view: View,
                              obj: UnionModelType) -> bool:
        # get concrete permission for model instance
        permission = CompanyMembershipPermissionsMap.get_permission_for_obj(obj)
        
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.company_membership.is_company_owner
            or request.user.company_membership.has_permission(permission)
        )


class IsCompanyOwnerOrReadOnly(permissions.BasePermission):
    
    def has_permission(self, request: Request, view: View) -> bool:
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.company_membership.is_company_owner
        )


class HasEmailConfirmed(permissions.BasePermission):
    
    def has_permission(self, request: Request, view: View) -> bool:
        return request.user.email_confirmed
