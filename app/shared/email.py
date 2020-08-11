from django.conf import settings

from templated_email import send_templated_mail


class Email:
    _SENT_FROM = settings.EMAIL_SENT_FROM
    _CLIENT_SITE_BASE_URL = settings.CLIENT_SITE_BASE_URL

    @classmethod
    def send_email_addr_confirm_email(cls, recipient_email: str,
                                      confirmation_token: str) -> None:
        confirm_email_url = \
            f'{cls._CLIENT_SITE_BASE_URL}/email-confirm/{confirmation_token}'

        send_templated_mail(
            template_name='email_addr_confirmation',
            from_email=cls._SENT_FROM,
            recipient_list=[recipient_email],
            context={'confirm_email_url': confirm_email_url},
        )

    @classmethod
    def send_company_invitation_email(cls, recipient_email: str,
                                      invitation_token: str,
                                      company_name: str) -> None:
        register_via_invitation_url = \
            f'{cls._CLIENT_SITE_BASE_URL}/register/{invitation_token}'

        send_templated_mail(
            template_name='company_invitation',
            from_email=cls._SENT_FROM,
            recipient_list=[recipient_email],
            context={
                'company_name': company_name,
                'registration_url': register_via_invitation_url
            }
        )

    @classmethod
    def send_password_reset_email(cls, recipient_email: str,
                                  password_reset_token: str) -> None:
        password_reset_url = \
            f'{cls._CLIENT_SITE_BASE_URL}/reset-password/{password_reset_token}'

        send_templated_mail(
            template_name='password_reset',
            from_email=cls._SENT_FROM,
            recipient_list=[recipient_email],
            context={'password_reset_url': password_reset_url}
        )
