from typing import Callable, Hashable, Generator, Any


def extract_values_from_dict_gen(target: dict,
                                 key: Hashable) -> Generator[Any, None, None]:
    """
    This function receives a dictionary, a key to search for 
    and returns a generator instance.
    The returned generator recursevly traverses a dictionary structure
    in a DFS PreOrder manner.
    
    1) To get all matching key values the returned generator must be iterated over
    till exaustion (by calling list() for example).
    2) To get a single (first encountered) mathing key value just call next()
    on the returned generator (do not forget to catch StopIteration exception
    if no matching results were found)
    """
    if isinstance(target, dict):
        for k, v in target.items():
            if k == key:
                yield v
            if isinstance(v, (dict, list)):
                yield from extract_values_from_dict_gen(v, key)
    elif isinstance(target, list):
        for d in target:
            yield from extract_values_from_dict_gen(d, key)


def transform_values_gen(gen: Generator,
                         predicate: Callable) -> Generator[Any, None, None]:
    """
    Given a generator instance iterate over it
    and apply provided predicate to each yielded value
    """
    for value in gen:
        yield predicate(value)
