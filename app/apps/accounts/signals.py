import logging
import threading
from smtplib import SMTPException

import sentry_sdk
from django.conf import settings
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from django.db.models.signals import post_save
from rest_framework.exceptions import APIException

from shared.email import Email
from utils.decorators import close_db_connections_when_finished
from apps.accounts.models import UserProfile, CompanyInvitation

# All signal handlers should be refactored to use celery workers
# instead of threads to free up main server process resources
# for request handling only

logger = logging.getLogger(__name__)

User = get_user_model()


@close_db_connections_when_finished
def send_password_reset_email_task(user_instance: User) -> None:
    try:
        Email.send_password_reset_email(
            password_reset_token=user_instance.unhashed_password_reset_token,
            recipient_email=user_instance.email
        )
    except SMTPException:
        sentry_sdk.capture_exception()
        user_instance.clear_password_reset_token()
        user_instance.save()


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(instance: User, created: bool, **kwargs) -> None:
    # automatically create user profile for user after registration
    if created:
        UserProfile.objects.create(profile_owner=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def send_password_reset_email(instance: User, created: bool,
                              update_fields: dict, **kwargs) -> None:
    # send email only when "password_reset_token" field
    # on the user model was updated
    if not created and update_fields and 'password_reset_token' in update_fields:
        thread = threading.Thread(
            target=send_password_reset_email_task,
            args=(instance,)
        )
        thread.start()


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def send_email_address_confirmation_email(instance: User, created: bool,
                                          update_fields: dict, **kwargs) -> None:
    # send email only after company and company owner was created
    # or user changed his email address
    if (
        (created and not instance.email_confirmed) or
        (update_fields and 'email' in update_fields)
    ):
        thread = threading.Thread(
            target=Email.send_email_addr_confirm_email,
            args=(instance.email, instance.email_confirmation_token),
        )
        thread.start()


@receiver(post_save, sender=CompanyInvitation)
def send_company_invitation_email(instance: CompanyInvitation,
                                  created: bool, **kwargs) -> None:
    # send email only when a potential company member is first invited
    if not created:
        return
    try:
        Email.send_company_invitation_email(
            recipient_email=instance.email,
            invitation_token=instance.unhashed_invitation_token,
            company_name=instance.company.company_name,
        )
    except SMTPException as e:
        logger.exception(e)
        # delete invitation instance and raise a 500 error code
        # if there was an error sending email
        instance.delete()
        raise APIException('Internal Server Error')
