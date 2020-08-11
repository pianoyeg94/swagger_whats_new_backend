import threading
from queue import Queue
from threading import Event
from collections import namedtuple, defaultdict

import celery

from django.db import transaction, DatabaseError
from django.db.models import Q, Prefetch

from config.celery import app
from utils.decorators import close_db_connections_when_finished
from apps.swagger_projects.workers import workers
from apps.swagger_projects.models import (
    SwaggerFile,
    RemoteVCSAccount,
    SwaggerFileChange
)


class TaskWithRetryOnDBError(celery.Task):
    autoretry_for = (DatabaseError,)
    retry_kwargs = {'max_retries': 3, 'countdown': 3}


@close_db_connections_when_finished
def pull_and_process_swagger_file_changes_producer(task_queue: Queue,
                                                   event: Event) -> None:
    """
    Query specific swagger file DB entities
    together with their related swagger projects
    and partialy initialized swagger file changes
    (have only related commit details).
    
    Package swagger file instances with their related swagger projects
    and swagger file changes into a task
    and pass it on to ProcessSwaggerFileDiffsWorker
    via a queue for further processing.
    """
    
    # prefetch swagger file changes that have not yet been processed
    # but registered some remote VCS account commits
    # via provided webhook callback.
    prefetch = Prefetch(
        'swagger_project__swagger_file_changes',
        queryset=SwaggerFileChange.objects.filter(swagger_file_changes={}),
        to_attr='swagger_file_changes_queryset'
    )
    
    # query swagger files related to swagger projects
    # which are not integrated with a remote VCS account
    # as well as swagger files related to swagger projects
    # integrated with remote VCS accounts that had recent commits
    # and may have triggered swagger file changes.
    
    # Prefetch related swagger projects and swagger file changes
    # for swagger projects integrated with VCS accounts
    # (swagger file change entities only with related commit details provided) -
    # prefetched entities will be used by ProcessSwaggerFileDiffsWorker.
    swagger_file_queryset = (
        SwaggerFile.objects.select_related(
            'swagger_project'
        )
        .prefetch_related(prefetch)
        .filter(
            Q(swagger_project__use_vcs=False) |
            Q(swagger_project__swagger_file_changes__swagger_file_changes={})
        )
        .distinct('id')
    )
    
    # package each swagger file instance from the previous queryset into a task
    # and pass it on to ProcessSwaggerFileDiffsWorker
    # via a thread safe queue for further processing
    for swagger_file_obj in swagger_file_queryset:
        Task = namedtuple(
            'Task',
            ['swagger_file_instance',
             'swagger_project_instance',
             'swagger_file_change_instance']
        )
        
        swagger_file_changes = \
            swagger_file_obj.swagger_project.swagger_file_changes_queryset
        swagger_file_change_instance = (swagger_file_changes[0]
                                        if swagger_file_changes
                                        else None)
        task = Task(
            swagger_file_obj,
            swagger_file_obj.swagger_project,
            swagger_file_change_instance
        )
        task_queue.put(task)
    
    # signal that no more tasks will be produced after this
    event.set()


@app.task(bind=True, base=TaskWithRetryOnDBError)
def pull_and_process_swagger_file_changes() -> None:
    """
    Launch producer and consumers in separate threads,
    delegate swagger file changes processing to consumer workers,
    collect results and persist them to DB.
    """
    
    task_queue = Queue()
    # 10 is the optimal number of workers,
    # if exceeded, performance begins to stagnate and then degrade
    num_consumers = 10
    event = threading.Event()
    # delegate the responsibility of defining required locks
    # to ProcessSwaggerFileDiffsWorker
    # these locks protect the "results_mapping" shared resource
    locks = defaultdict(threading.Lock)
    # delegate the responsibility of defining required result entities
    # to ProcessSwaggerFileDiffsWorker
    results_mapping = defaultdict(list)
    
    # start producing tasks
    producer = threading.Thread(
        target=pull_and_process_swagger_file_changes_producer,
        args=(task_queue, event)
    )
    producer.start()
    
    # start consuming tasks
    for _ in range(num_consumers):
        consumer = workers.ProcessSwaggerFileDiffsWorker(
            task_queue=task_queue,
            event=event,
            locks=locks,
            results_mapping=results_mapping
        )
        consumer.start()
    
    # wait for producer and all the consumers to be finished
    producer.join()
    task_queue.join()
    
    # collect results and save them to DB
    # do it within a transaction to avoid data inconsistency -
    # updated swagger files without registered swagger file changes
    with transaction.atomic():
        SwaggerFileChange.objects.bulk_update(
            results_mapping[workers.SWAGGER_FILE_CHANGES_TO_UPDATE],
            ['changes_added_at', 'swagger_file_changes'],
            batch_size=100
        )
        
        SwaggerFileChange.objects.bulk_create(
            results_mapping[workers.SWAGGER_FILE_CHANGES_TO_CREATE],
            batch_size=100
        )
        
        SwaggerFileChange.objects.filter(
            id__in=results_mapping[workers.SWAGGER_FILE_CHANGES_TO_DELETE]
        ).delete()
        
        SwaggerFile.objects.bulk_update(
            results_mapping[workers.SWAGGER_FILES_TO_UPDATE],
            ['swagger_file'],
            batch_size=100
        )


@close_db_connections_when_finished
def refresh_remote_vcs_account_access_token_producer(task_queue: Queue,
                                                     event: Event) -> None:
    """
    Query DB to get remote VCS accounts
    that require OAuth access token resfresh,
    delegate token refreshing to RefreshRemoteVCSAccountAccessTokenWorker
    via a thread safe queue.
    """
    
    # Filter out remote VCS accounts that do not require OAuth token refresh
    remote_vcs_account_queryset_gen = RemoteVCSAccount.objects.all().exclude(
        refresh_token__isnull=True).iterator()
    
    # Delegate token refresh to RefreshRemoteVCSAccountAccessTokenWorker
    # via a thread safe queue
    for remote_vcs_account in remote_vcs_account_queryset_gen:
        task_queue.put(remote_vcs_account)

    # signal that no more tasks will be produced after this
    event.set()


@app.task(bind=True, base=TaskWithRetryOnDBError)
def refresh_remote_vcs_account_access_token() -> None:
    """
    Launch producer and consumers in separate threads,
    delegate OAuth access token refresh to consumer workers,
    collect results and persist them to DB.
    """
    
    task_queue = Queue()
    # 10 is the optimal number of workers,
    # if exceeded, performance begins to stagnate and then degrade
    num_consumers = 10
    event = threading.Event()
    # lock that protects the "vcs_accounts_to_update" shared resource
    vcs_accounts_to_update_lock = threading.Lock()
    vcs_accounts_to_update = []
    
    # start producing
    producer = threading.Thread(
        target=refresh_remote_vcs_account_access_token_producer,
        args=(task_queue, event)
    )
    producer.start()
    
    # start consuming
    for _ in range(num_consumers):
        worker = workers.RefreshRemoteVCSAccountAccessTokenWorker(
            task_queue=task_queue,
            event=event,
            vcs_accounts_to_update=vcs_accounts_to_update,
            vcs_accounts_to_update_lock=vcs_accounts_to_update_lock
        )
        worker.start()

    # wait for producer and all the consumers to be finished
    producer.join()
    task_queue.join()

    # collect results and save them to DB
    RemoteVCSAccount.objects.bulk_update(
        vcs_accounts_to_update,
        ['access_token', 'refresh_token'],
        batch_size=300
    )
