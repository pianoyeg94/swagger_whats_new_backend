from enum import Enum
from typing import Union, Iterable

import hashlib
from itertools import chain, combinations


def sha256_hasher(value: Union[str, int, float]) -> str:
    hasher_instance = hashlib.sha256()
    hasher_instance.update(str.encode(value))
    hashed_value = hasher_instance.hexdigest()
    return hashed_value


def powerset(iterable: Iterable) -> Iterable:
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s) + 1))


def convert_enum_to_dict(enum: Union[Enum, Iterable],
                         lowercase_keys: bool = False) -> dict:
    d = (
        {e.name.lower(): e.value for e in enum}
        if lowercase_keys
        else {e.name: e.value for e in enum}
    )

    return d
