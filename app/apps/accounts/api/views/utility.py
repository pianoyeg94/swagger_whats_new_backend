from django.core.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request

from apps.accounts.models import User, Company, CompanyInvitation

"""
Utility views used by "our" frontend
to asynchronously validate form fields and url tokens.
"""


class SameUserException(Exception):
    """Utility exception used to exclude current user details during validation"""


class CheckEmailIsInUseAPIView(APIView):
    
    def post(self, request: Request) -> Response:
        user = request.user
        try:
            # exclude current user's email from validation
            if not user.is_anonymous and user.email == request.data['email']:
                raise SameUserException()
            
            User.objects.get(email=request.data['email'])
            return Response(data={'email_taken': True})
        except (User.DoesNotExist, SameUserException):
            return Response(data={'email_taken': False})


class CheckCompanyNameIsInUseAPIView(APIView):
    
    def post(self, request: Request) -> Response:
        user = request.user
        try:
            # exclude current user's company name from validation
            if (
                not user.is_anonymous and
                user.company.company_name == request.data['company_name']
            ):
                raise SameUserException()
            
            Company.objects.get(company_name=request.data['company_name'])
            return Response(data={'company_name_taken': True})
        except (Company.DoesNotExist, SameUserException):
            return Response(data={'company_name_taken': False})


class CheckPasswordResetTokenIsValidAPIView(APIView):
    
    def get(self, request: Request, password_reset_token: str) -> Response:
        try:
            User.objects.validate_get_by_password_reset_token(
                password_reset_token)
            return Response(data={'password_reset_token_valid': True})
        except ValidationError:
            return Response(data={'password_reset_token_valid': False})


class CheckCompanyInvitationTokenIsValidAPIView(APIView):
    
    def get(self, request: Request, company_invitation_token: str) -> Response:
        try:
            CompanyInvitation.objects.validate_get_by_invitation_token(
                company_invitation_token)
            return Response(data={'company_invitation_token_valid': True})
        except ValidationError:
            return Response(data={'company_invitation_token_valid': False})
