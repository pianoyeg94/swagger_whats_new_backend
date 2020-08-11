import threading

from django.dispatch import Signal, receiver
from django.db.models.signals import post_save, post_delete

from utils.decorators import close_db_connections_when_finished
from apps.swagger_projects.repo_commits_webhook_callback import RepositoryCommitsWebhookCallback
from apps.swagger_projects.models import (
    SwaggerProject,
    SwaggerFile,
    RemoteVCSAccount
)

# All signal handlers should be refactored to use celery workers
# instead of threads to free up main server process resources
# for request handling only

trigger_webhook_callback_signal = Signal(
    providing_args=["remote_vcs_service", "request_data"]
)


@close_db_connections_when_finished
def webhook_callback_task(remote_vcs_service_header: str,
                          request_data: dict) -> None:
    webhook_callback = RepositoryCommitsWebhookCallback(
        remote_vcs_service_header=remote_vcs_service_header,
        data=request_data
    )
    webhook_callback.initialize_callback()
    webhook_callback()


@receiver(post_save, sender=SwaggerProject)
def pull_create_swagger_file(instance: SwaggerProject, created: bool, **kwargs):
    """
    Runs when a swagger project is first created.
    Downloads swagger file and saves swagger file model instance to DB.
    """
    if created:
        # decorate method so that all "dangling" db connections
        # will be closed after task completion
        validate_create = close_db_connections_when_finished(
            SwaggerFile.objects.validate_create)
        thread = threading.Thread(target=validate_create, args=(instance,))
        thread.start()


@receiver(post_delete, sender=RemoteVCSAccount)
def revoke_access_token(instance: RemoteVCSAccount, **kwargs):
    """
    Runs when a RemoteVCSAccount model instance is deleted.
    Revokes corresponding OAuth token
    """
    thread = threading.Thread(target=instance.revoke_access_token)
    thread.start()


@receiver(post_delete, sender=SwaggerProject)
def delete_webhook(instance: SwaggerProject, **kwargs):
    """
    Runs when a SwaggerProject model instance is deleted.
    Deletes corresponding webhook from associated repository if any
    """
    delete_repo_webhook = close_db_connections_when_finished(
        instance.delete_repo_webhook)
    thread = threading.Thread(target=delete_repo_webhook)
    thread.start()


@receiver(trigger_webhook_callback_signal)
def trigger_webhook_callback(remote_vcs_service_header: str,
                             request_data: dict, **kwargs):
    """
    Runs when a commit to a tracked VCS repository was registered
    (tracked by SwaggerProject entity).
    
    Processes webhook data and partialy "initializes"
    a new SwaggerFileChange model instance
    with only related commit details provided
    """
    thread = threading.Thread(
        target=webhook_callback_task,
        args=(remote_vcs_service_header, request_data)
    )
    thread.start()
