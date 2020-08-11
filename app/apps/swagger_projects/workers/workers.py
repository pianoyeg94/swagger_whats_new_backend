import threading
import logging
from threading import Event, Lock
from queue import Queue
from requests.exceptions import ConnectionError
from typing import List, DefaultDict

from django.apps import apps
from django.utils import timezone

from .data_pipelines import SwaggerFileDiffsPipeline
from apps.swagger_projects.models import SwaggerFileChange, RemoteVCSAccount
from .helpers import (
    create_endpoints_contract_mapping,
    create_nested_contracts_mapping
)

SWAGGER_FILE_CHANGES_TO_CREATE = 'swagger_file_changes_to_create'
SWAGGER_FILE_CHANGES_TO_UPDATE = 'swagger_file_changes_to_update'
SWAGGER_FILE_CHANGES_TO_DELETE = 'swagger_file_changes_to_delete'
SWAGGER_FILES_TO_UPDATE = 'swagger_files_to_update'

APP = apps.get_app_config('swagger_projects')
http = APP.http
logger = logging.getLogger(__name__)


class ProcessSwaggerFileDiffsWorker(threading.Thread):
    """
    Worker that processes swagger file changes
    and prepares them to be saved to DB.
    
    1) Get task from queue
    (task includes swagger file model instance, related swagger project,
    partialy initialized swagger file change
    if swagger project is integrated with a remote VCS account).
    
    2) Download current swagger file version for swagger project.
    
    3) Generate 2 mappings (required for swagger file changes processing):
        1.  Mapping that associates endpoints with their corresponding contracts.
        2.  Mapping that provides information
            about contracts nested in other contracts.
            
    4) Calculate swagger file differences by comparing 2 swagger files -
       swagger file stored in "our" system
       and downloaded swagger file (current version).
       
       Interprate these changes (additions or removals in endpoints, methods,
       contracts, contract properties).
       
       Store changes in a dictionary to be persisted to the database.
       
    5) Prepare swagger file changes
    and related business logic entities to be persisted to DB
    (update or create new swagger file change entity,
    delete swagger file change entity if no changes were registered,
    replace swagger file stored in the database with its new version
    if swagger file changes were registered).
    """
    
    _SWAGGER_FILE_CHANGES_TO_CREATE_LOCK = 'swagger_file_changes_to_create_lock'
    _SWAGGER_FILE_CHANGES_TO_UPDATE_LOCK = 'swagger_file_changes_to_update_lock'
    _SWAGGER_FILE_CHANGES_TO_DELETE_LOCK = 'swagger_file_changes_to_delete_lock'
    _SWAGGER_FILES_TO_UPDATE_LOCK = 'swagger_files_to_update_lock'
    
    def __init__(self, task_queue: Queue,
                 event: Event,
                 locks: DefaultDict[str, Lock],
                 results_mapping: DefaultDict[str, list]):
        threading.Thread.__init__(self)
        self.task_queue = task_queue
        self.event = event
        self.locks = locks
        self.results_mapping = results_mapping
        
        self.swagger_file_changes = None
        self.swagger_file_instance = None
        self.swagger_project_instance = None
        self.swagger_file_change_instance = None
        self.current_swagger_file_version = None
        self.new_swagger_file_version = None
        self.endpoint_contract_mapping = None
        self.nested_contracts_mapping = None
    
    def run(self) -> None:
        while not self.event.is_set() or not self.task_queue.empty():
            self.get_store_task_from_queue()
            
            try:
                self.load_store_swagger_files()
            except ConnectionError as e:
                logging.exception(e)
            else:
                self.generate_set_mandatory_mappings()
                self.run_swagger_file_diffs_pipeline()
                self.prepare_swagger_file_changes_to_be_saved_to_db()
            finally:
                self.task_queue.task_done()
    
    def get_store_task_from_queue(self) -> None:
        task = self.task_queue.get()
        self.swagger_file_instance = task.swagger_file_instance
        self.swagger_project_instance = task.swagger_project_instance
        self.swagger_file_change_instance = task.swagger_file_change_instance
    
    def load_store_swagger_files(self) -> None:
        self.current_swagger_file_version = \
            self.swagger_file_instance.swagger_file
        self.new_swagger_file_version = http.get(
            self.swagger_project_instance.swagger_file_url).json()
    
    def generate_set_mandatory_mappings(self) -> None:
        paths = self.new_swagger_file_version['paths']
        contracts = self.new_swagger_file_version['definitions']
        self.endpoint_contract_mapping = create_endpoints_contract_mapping(paths)
        self.nested_contracts_mapping = create_nested_contracts_mapping(contracts)
    
    def run_swagger_file_diffs_pipeline(self) -> None:
        pipe = SwaggerFileDiffsPipeline(
            current_swagger_file_version=self.current_swagger_file_version,
            new_swagger_file_version=self.new_swagger_file_version,
            endpoint_contract_mapping=self.endpoint_contract_mapping,
            nested_contracts_mapping=self.nested_contracts_mapping,
        )
        pipe.run()
        self.swagger_file_changes = pipe.swagger_file_changes
    
    def prepare_swagger_file_changes_to_be_saved_to_db(self) -> None:
        # if at least a single swagger file change was registered,
        # prepare it to be persisted to the database
        if any(
            (*self.swagger_file_changes['additions'].values(),
             *self.swagger_file_changes['removals'].values())
        ):
            # if swagger project is integrated with a remote VCS account,
            # update the current swagger file change instance
            # to include "discovered" swagger file changes
            if self.swagger_file_change_instance:
                self._prepare_changes_for_update()
            # if swagger project is not integrated with a remote VCS account
            # create a new swagger file change model instance
            else:
                self._prepare_changes_for_creation()
            
            # replace swagger file with its new version
            self._prepare_files_for_update()
        else:
            if not self.swagger_file_change_instance:
                return
            
            # if swagger project is integrated with a remote VCS account
            # and no swagger file changes were registered,
            # prepare partialy initialized swagger file change to be deleted
            self._prepare_changes_for_deletion()
    
    def _prepare_changes_for_creation(self) -> None:
        swagger_file_change = SwaggerFileChange(
            swagger_project=self.swagger_project_instance,
            swagger_file_changes=self.swagger_file_changes,
            changes_added_at=timezone.now()
        )
        
        with self.locks[self._SWAGGER_FILE_CHANGES_TO_CREATE_LOCK]:
            self.results_mapping[SWAGGER_FILE_CHANGES_TO_CREATE].append(
                swagger_file_change)
    
    def _prepare_changes_for_update(self) -> None:
        self.swagger_file_change_instance.changes_added_at = timezone.now()
        self.swagger_file_change_instance.swagger_file_changes = \
            self.swagger_file_changes
        
        with self.locks[self._SWAGGER_FILE_CHANGES_TO_UPDATE_LOCK]:
            self.results_mapping[SWAGGER_FILE_CHANGES_TO_UPDATE].append(
                self.swagger_file_change_instance)
    
    def _prepare_changes_for_deletion(self) -> None:
        with self.locks[self._SWAGGER_FILE_CHANGES_TO_DELETE_LOCK]:
            self.results_mapping[SWAGGER_FILE_CHANGES_TO_DELETE].append(
                self.swagger_file_change_instance.id)
    
    def _prepare_files_for_update(self) -> None:
        self.swagger_file_instance.swagger_file = self.new_swagger_file_version
        
        with self.locks[self._SWAGGER_FILES_TO_UPDATE_LOCK]:
            self.results_mapping[SWAGGER_FILES_TO_UPDATE].append(
                self.swagger_file_instance)


class RefreshRemoteVCSAccountAccessTokenWorker(threading.Thread):
    """
    Worker that refreshes OAuth access tokens
    and prepares new access tokens to be saved to DB.
    """
    
    def __init__(self, task_queue: Queue,
                 event: Event,
                 vcs_accounts_to_update_lock: Lock,
                 vcs_accounts_to_update: List[RemoteVCSAccount]):
        threading.Thread.__init__(self)
        self.task_queue = task_queue
        self.event = event
        self.vcs_accounts_to_update_lock = vcs_accounts_to_update_lock
        self.vcs_accounts_to_update = vcs_accounts_to_update
    
    def run(self) -> None:
        while not self.event.is_set() or not self.task_queue.empty():
            remote_vcs_account = self.task_queue.get()
            
            try:
                remote_vcs_account.refresh_access_token()
            except ConnectionError as e:
                logging.exception(e)
            else:
                with self.vcs_accounts_to_update_lock:
                    self.vcs_accounts_to_update.append(remote_vcs_account)
            finally:
                self.task_queue.task_done()
