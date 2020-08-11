from .base import *

DEBUG = True

# Email related settings
EMAIL_HOST = 'smtp.mailtrap.io'
EMAIL_USE_TLS = False
EMAIL_PORT = 587
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_SENT_FROM = os.environ.get('EMAIL_SENT_FROM')