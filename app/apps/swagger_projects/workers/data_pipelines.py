from contextlib import contextmanager
from typing import Callable, Generator, Tuple, List, Dict, Union

import dictdiffer

from utils.decorators import coroutine
from .helpers import HelperMapping

SwaggerDiff = Tuple[str, Union[str, List[Union[str, int]]], tuple]
TransfomedDiff = Dict[str, List[str]]
FilterPredicate = Callable[[SwaggerDiff], bool]
PipeSink = Generator[None, TransfomedDiff, None]
PipeStage = Generator[None, SwaggerDiff, None]


class SwaggerFileDiffsPipeline:
    """
    Split swagger file difference processing in to multiple pipeline stages,
    these stages are supposed to be easily swapped out and added if needed.
    
    dictdiffer library does all the heavy lifting of traversing
    and comparing json trees. Pipeline stages interprate the resulting differences
    """
    
    def __init__(self, current_swagger_file_version: dict,
                 new_swagger_file_version: dict,
                 endpoint_contract_mapping: HelperMapping,
                 nested_contracts_mapping: HelperMapping):
        self.current_swagger_file_version = current_swagger_file_version
        self.new_swagger_file_version = new_swagger_file_version
        self.endpoint_contract_mapping = endpoint_contract_mapping
        self.nested_contracts_mapping = nested_contracts_mapping
        self.swagger_file_changes = dict(
            removals=dict(endpoints=[], methods=[],
                          contracts=[], contract_properties=[]),
            additions=dict(endpoints=[], methods=[],
                           contracts=[], contract_properties=[])
        )
    
    def run(self) -> None:
        with self.pipeline() as pipe:
            swagger_file_diffs_gen = dictdiffer.diff(
                self.current_swagger_file_version,
                self.new_swagger_file_version
            )
            
            # send each swagger file change to pipeline coroutine
            for diff in swagger_file_diffs_gen:
                pipe.send(diff)
    
    @contextmanager
    def pipeline(self):
        pipe = self.pipeline_coro()
        try:
            yield pipe
        finally:
            pipe.close()
    
    @coroutine
    def pipeline_coro(self) -> PipeStage:
        """
        Pull all the different pipeline stages together into a single pipeline
        """
        addition_endpoints = self.save_diff('additions', 'endpoints')
        addition_methods = self.save_diff('additions', 'methods')
        addition_contracts = self.save_diff('additions', 'contracts')
        addition_contract_properties = self.save_diff(
            'additions',
            'contract_properties'
        )
        
        removal_endpoints = self.save_diff('removals', 'endpoints')
        removal_methods = self.save_diff('removals', 'methods')
        removal_contracts = self.save_diff('removals', 'contracts')
        removal_contract_properties = self.save_diff(
            'removals',
            'contract_properties'
        )
        
        additions_endpoint_diff = self.endpoint_diff_transformer(
            addition_endpoints)
        additions_method_diff = self.method_diff_transformer(addition_methods)
        additions_contract_diff = self.contract_diff_transformer(
            addition_contracts)
        additions_contract_properties_diff = self.contract_properties_diff_transformer(
            addition_contract_properties)
        
        removals_endpoint_diff = self.endpoint_diff_transformer(removal_endpoints)
        removals_method_diff = self.method_diff_transformer(removal_methods)
        removals_contract_diff = self.contract_diff_transformer(removal_contracts)
        removals_contract_properties_diff = self.contract_properties_diff_transformer(
            removal_contract_properties)
        
        additions_router = self.route_to_transformers(
            endpoint_diff=additions_endpoint_diff,
            method_diff=additions_method_diff,
            contract_diff=additions_contract_diff,
            contract_properties_diff=additions_contract_properties_diff,
        )
        
        removals_router = self.route_to_transformers(
            endpoint_diff=removals_endpoint_diff,
            method_diff=removals_method_diff,
            contract_diff=removals_contract_diff,
            contract_properties_diff=removals_contract_properties_diff,
        )
        
        filter_removals = self.filter_diff(
            lambda diffr: diffr[0] == 'remove',
            removals_router
        )
        filter_additions = self.filter_diff(
            lambda diffr: diffr[0] == 'add',
            additions_router
        )
        
        filters = (filter_removals, filter_additions)
        
        broadcaster = self.broadcast(filters)
        
        while True:
            diff = yield
            broadcaster.send(diff)
    
    @coroutine
    def broadcast(self, targets: Tuple[PipeStage, ...]) -> PipeStage:
        """Broadcast each swagger file change to filters for further processing"""
        while True:
            diff = yield
            for target in targets:
                target.send(diff)
    
    @coroutine
    def filter_diff(self, filter_predicate: FilterPredicate,
                    target: PipeStage) -> PipeStage:
        """
        Filter swagger file change based on the provided predicate
        and pass it down to corresponding router stage
        """
        while True:
            diff = yield
            if filter_predicate(diff):
                target.send(diff)
    
    @coroutine
    def route_to_transformers(self, contract_properties_diff: PipeStage,
                              endpoint_diff: PipeStage,
                              contract_diff: PipeStage,
                              method_diff: PipeStage) -> PipeStage:
        """
        Route swagger file change to data transformation stages
        based on 4 criterias:
        1) Endpoint change
        2) Method change
        3) Contract change
        4) Contract properties change
        """
        while True:
            diff = yield
            where = diff[1]
            
            # endpoints
            if where.endswith('paths'):
                endpoint_diff.send(diff)
            # contracts
            elif where.endswith('definitions'):
                contract_diff.send(diff)
            # methods
            elif where.startswith('paths'):
                method_diff.send(diff)
            # contract properties
            elif where.endswith('properties'):
                contract_properties_diff.send(diff)
    
    @coroutine
    def endpoint_diff_transformer(self, target: PipeSink) -> PipeStage:
        """
        Format endpoint change to adhere to the following format:
        {"where": "path", "what": <added/removed endpoint>}
        
        Pass down to sink stage to be saved to results dictionary
        """
        while True:
            diff = yield
            where = diff[1]
            what = [el[0] for el in diff[2]]
            target.send(dict(where=where, what=what))
    
    @coroutine
    def method_diff_transformer(self, target: PipeSink) -> PipeStage:
        """
        Format method change to adhere to the following format:
        {"where": <endpoint>, "what": <added/removed method>}

        Pass down to sink stage to be saved to results dictionary
        """
        while True:
            diff = yield
            where = diff[1].split('.')[-1]
            what = [el[0] for el in diff[2]]
            target.send(dict(where=where, what=what))
    
    @coroutine
    def contract_diff_transformer(self, target: PipeSink) -> PipeStage:
        """
        Format contract change to adhere to the following format:
        {"where": "definitions", "what": <added/removed contract>}

        Pass down to sink stage to be saved to results dictionary
        """
        while True:
            diff = yield
            where = diff[1]
            what = [el[0] for el in diff[2]]
            target.send(dict(where=where, what=what))
    
    @coroutine
    def contract_properties_diff_transformer(self, target: PipeSink) -> PipeStage:
        """
        Format contract properties change to adhere to the following format:
        {
            "where": {
                "contract": <contract>,
                "enpoints": <list of endpoints in which this contract is used>
                "nested_in_other_contracts": <list of contracts
                                              in which this contract is nested>
            },
            "what": <added/removed contract properties>
        }

        Pass down to sink stage to be saved to results dictionary
        """
        while True:
            diff = yield
            where = diff[1].split('.')[-2]
            what = [el[0] for el in diff[2]]
            new_where = dict()
            nested_in_contracts = [k for k, v
                                   in self.nested_contracts_mapping.items()
                                   if where in v]
            
            new_where['contract'] = where
            new_where['endpoints'] = self.endpoint_contract_mapping.get(where)
            new_where['nested_in_other_contracts'] = \
                nested_in_contracts if nested_in_contracts else None
            
            target.send(dict(where=new_where, what=what))
    
    @coroutine
    def save_diff(self, change_type: str, where: str) -> PipeSink:
        """
        Recieve transformed and formatted swagger file change
        and save to results dictionary
        """
        while True:
            change = yield
            self.swagger_file_changes[change_type][where].append(change)
