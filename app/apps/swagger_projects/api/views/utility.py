from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request

from apps.swagger_projects.models import RemoteVCSAccount, SwaggerProject

"""
Utility views used by "our" frontend
to asynchronously validate form fields
"""


class CheckUniqueVCSAccountAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    
    def post(self, request: Request) -> Response:
        try:
            RemoteVCSAccount.objects.get(
                **request.data,
                company_id=request.user.company_id
            )
            return Response(data={'vcs_account_exists': True})
        except RemoteVCSAccount.DoesNotExist:
            return Response(data={'vcs_account_exists': False})


class CheckUniqueSwaggerProjectNameAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    
    def post(self, request: Request) -> Response:
        try:
            SwaggerProject.objects.get(
                **request.data,
                company_id=request.user.company_id
            )
            return Response(data={'swagger_project_name_taken': True})
        except SwaggerProject.DoesNotExist:
            return Response(data={'swagger_project_name_taken': False})


class CheckUniqueRepoBranchAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    
    def post(self, request: Request) -> Response:
        try:
            SwaggerProject.objects.get(
                **request.data,
                company_id=request.user.company_id
            )
            return Response(data={'branch_already_registered': True})
        except SwaggerProject.DoesNotExist:
            return Response(data={'branch_already_registered': False})
