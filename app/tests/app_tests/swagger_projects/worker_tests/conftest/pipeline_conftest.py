import os
import json
from typing import Tuple, Any, Generator, Callable

from pytest import fixture

from django.conf import settings

from utils.decorators import coroutine
from apps.swagger_projects.workers.data_pipelines import SwaggerFileDiffsPipeline
from apps.swagger_projects.workers.helpers import (
    create_endpoints_contract_mapping,
    create_nested_contracts_mapping
)

HELPER_FILES_DIR = os.path.join(settings.BASE_DIR, 'tests', 'helper_files')

PATH_TO_CURRENT_SWAGGER_FILE_VERSION = os.path.join(
    HELPER_FILES_DIR,
    'current_swagger_file_version.json'
)

PATH_TO_NEW_SWAGGER_FILE_VERSION = os.path.join(
    HELPER_FILES_DIR,
    'new_swagger_file_version.json'
)

PATH_TO_CONTRACT_PROP_DIFFS = os.path.join(
    HELPER_FILES_DIR,
    'contract_prop_diffs.json'
)

PATH_TO_PIPELINE_RESULTS = os.path.join(
    HELPER_FILES_DIR,
    'pipeline_results.json'
)


def append_and_return_value(lst: list, value: Any) -> Any:
    lst.append(value)
    return value


def sink_for_test_results() -> Tuple[Generator[None, Any, None], list]:
    """
    A factory function for generator based coroutines
    that will be used to recieve and store individual test results
    from other generator based coroutines under test.
    
    Gives access to the "results" list from outside
    by returning it together with the primed coroutine.
    """
    
    results = []
    
    @coroutine
    def sink():
        while True:
            result = yield
            results.append(result)
    
    return sink(), results


@fixture(scope='session')
def sink_factory() -> Generator[Callable, None, None]:
    """
    This fixture yields a callable
    that returns a new copy of a generator based coroutine (results sink)
    and a results list.
    
    At the same time it keeps track of all the yielded coroutines
    via the "sink_tuples" list.
    This allows it to automatically close all the coroutines
    after the test session completes.
    """
    
    sink_tuples = []
    yield lambda: append_and_return_value(sink_tuples, sink_for_test_results())
    for sink, _ in sink_tuples:
        sink.close()


@fixture(scope='session')
def swagger_files() -> Tuple[dict, dict]:
    with open(PATH_TO_CURRENT_SWAGGER_FILE_VERSION) as current:
        current_version = json.load(current)
    
    with open(PATH_TO_NEW_SWAGGER_FILE_VERSION) as new:
        new_version = json.load(new)
    
    return current_version, new_version


@fixture(scope='session')
def precalculated_results() -> dict:
    results = {}
    
    with open(PATH_TO_CONTRACT_PROP_DIFFS) as result:
        results['contract_prop_diffs'] = json.load(result)
    
    with open(PATH_TO_PIPELINE_RESULTS) as result:
        results['pipeline_results'] = json.load(result)
    
    return results


@fixture(scope='session')
def mandatory_mappings(swagger_files) -> Tuple[dict, dict]:
    _, new_version = swagger_files
    
    paths = new_version['paths']
    contracts = new_version['definitions']
    
    endpoint_contract_mapping = create_endpoints_contract_mapping(paths)
    nested_contracts_mapping = create_nested_contracts_mapping(contracts)
    
    return endpoint_contract_mapping, nested_contracts_mapping


@fixture
def swagger_file_diffs_pipeline(
    swagger_files: Tuple[dict, dict],
    mandatory_mappings: Tuple[dict, dict]
) -> SwaggerFileDiffsPipeline:
    current_version, new_version = swagger_files
    endpoint_contract_mapping, nested_contracts_mapping = mandatory_mappings
    
    pipe = SwaggerFileDiffsPipeline(
        current_swagger_file_version=current_version,
        new_swagger_file_version=new_version,
        endpoint_contract_mapping=endpoint_contract_mapping,
        nested_contracts_mapping=nested_contracts_mapping,
    )
    
    return pipe
