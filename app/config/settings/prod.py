import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.django import DjangoIntegration

from .base import *

DEBUG = False

# tell Django to look for X-Forwarded-Proto Nginx header
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# for kubernetes readiness and liveness probes
ALLOWED_HOSTS.append(os.environ.get('POD_IP'))

# Sentry related settings
sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN'),
    integrations=[DjangoIntegration(), LoggingIntegration()],
    send_default_pii=True
)

# Email related settings
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_SENT_FROM = os.environ.get('EMAIL_SENT_FROM')