from typing import Dict, Mapping, List

from utils.generators import extract_values_from_dict_gen, transform_values_gen

HelperMapping = Dict[str, List[str]]
SwaggerSection = Mapping[str, dict]


def create_endpoints_contract_mapping(paths: SwaggerSection) -> HelperMapping:
    """
    Create and return dictionary
    that maps API endpoints to their corresponding contracts
    """
    endpoint_contract_mapping = dict()
    
    for path, methods in paths.items():
        for method, details in methods.items():
            # find value for key "$ref" - it points to contract that is being used
            contract_gen = extract_values_from_dict_gen(details, '$ref')
            transformed_contract_gen = transform_values_gen(
                contract_gen,
                lambda c: c.split('/')[-1]
            )
            
            try:
                contract = next(transformed_contract_gen)
            except StopIteration:
                continue
            
            endpoint_contract_mapping.setdefault(contract, []).append(
                f'{method} {path}')
    
    return endpoint_contract_mapping


def create_nested_contracts_mapping(contracts: SwaggerSection) -> HelperMapping:
    """
    Create and return dictionary
    that contains contracts as keys
    and their corresponding nested contracts as values if any
    """
    nested_contracts_mapping = dict()
    
    for k, v in contracts.items():
        # find all values for key "$ref" -
        # they point to contracts that are being used
        contract_gen = extract_values_from_dict_gen(v, '$ref')
        transformed_contract_gen = transform_values_gen(
            contract_gen,
            lambda c: c.split('/')[-1]
        )
        
        if contracts := list(transformed_contract_gen):
            nested_contracts_mapping[k] = contracts
    
    return nested_contracts_mapping
