from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from shared.permissions import IsCompanyOwnerOrReadOnly
from apps.accounts.api.serializers import CompanySerializer
from apps.accounts.models import Company


class CompanyRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CompanySerializer
    permission_classes = (IsAuthenticated, IsCompanyOwnerOrReadOnly)

    def perform_destroy(self, instance: Company) -> None:
        instance.delete_company_account()

    def get_object(self) -> Company:
        return self.request.user.company
