from django.utils import timezone

from config.celery import app
from apps.accounts.models import CompanyInvitation


@app.task
def delete_expired_company_invitations() -> None:
    queryset = CompanyInvitation.objects.filter(
        invitation_expires__lt=timezone.now())
    queryset.delete()
