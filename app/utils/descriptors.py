from enum import EnumMeta
from numbers import Real
from typing import List

from .functions import powerset


class EnumAttrValuesSum:
    """
    Non-data descriptor that sums up all enum field values
    if they are real numbers.
    """
    
    def __init__(self):
        # no need for a weak reference, will not be used with instances
        self.cached_value = None

    def __get__(self, instance: None, owner_class: EnumMeta) -> Real:
        if instance is not None:
            raise AttributeError('Attribute not accessible from instance.')

        if not type(owner_class) is EnumMeta:
            raise TypeError('Class must be of type Enum.')

        if not self.cached_value:
            real_numbers_in_enum_values = [e.value for e in owner_class 
                                           if isinstance(e.value, Real)]
            if len(owner_class) != len(real_numbers_in_enum_values):
                raise TypeError('Enum values must include only real numbers.')

            self.cached_value = sum(e.value for e in owner_class)

        return self.cached_value


class EnumAttrValueCombinations:
    """
    Non-data descriptor that sums up all possible enum field value permutations
    if they are real numbers.
    """
    
    def __init__(self):
        # no need for a weak reference, will not be used with instances
        self.cached_value = None

    def __get__(self, instance: None, owner_class: EnumMeta) -> List[Real]:
        if instance is not None:
            raise AttributeError('Attribute not accessible from instance.')

        if not type(owner_class) is EnumMeta:
            raise TypeError('Class must be of type Enum.')

        if not self.cached_value:
            real_numbers_in_enum_values = [e.value for e in owner_class 
                                           if isinstance(e.value, Real)]
            if len(owner_class) != len(real_numbers_in_enum_values):
                raise TypeError('Enum values must include only real numbers.')

            values_gen = (e.value for e in owner_class)
            self.cached_value = sorted([sum(s) for s in powerset(values_gen) if s])

        return self.cached_value
