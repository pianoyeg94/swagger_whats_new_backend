import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', os.environ['DJANGO_SETTINGS_MODULE'])

app = Celery('swagger_whats_new')
app.config_from_object('django.conf:settings')

app.autodiscover_tasks()

DELETE_EXPIRED_COMPANY_INVITATIONS_CRON = os.environ.get(
    'DELETE_EXPIRED_COMPANY_INVITATIONS_CRON')
PULL_AND_PROCESS_SWAGGER_FILE_CHANGES_CRON = os.environ.get(
    'PULL_AND_PROCESS_SWAGGER_FILE_CHANGES_CRON')
REFRESH_REMOTE_VCS_ACCOUNT_ACCESS_TOKEN_CRON = os.environ.get(
    'REFRESH_REMOTE_VCS_ACCOUNT_ACCESS_TOKEN_CRON')

app.conf.beat_schedule = {
    'delete_expired_company_invitations': {
        'task': 'apps.accounts.tasks.delete_expired_company_invitations',
        'schedule': crontab(minute=f'*/{DELETE_EXPIRED_COMPANY_INVITATIONS_CRON}'),
    },
    'pull_and_process_swagger_file_changes': {
        'task': 'apps.swagger_projects.tasks.pull_and_process_swagger_file_changes',
        'schedule': crontab(minute=f'*/{PULL_AND_PROCESS_SWAGGER_FILE_CHANGES_CRON}'),
    },
    'refresh_remote_vcs_account_access_token': {
        'task': 'apps.swagger_projects.tasks.refresh_remote_vcs_account_access_token',
        'schedule': crontab(minute=f'*/{REFRESH_REMOTE_VCS_ACCOUNT_ACCESS_TOKEN_CRON}'),
    },
}
