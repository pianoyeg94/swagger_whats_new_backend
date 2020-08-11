from typing import OrderedDict, Iterable, Union

from django.db.models import QuerySet, Model
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.serializers import Serializer


class FieldsEqualityValidator:
    """Given any number of serializer fields validate that all values are equal"""
    
    def __init__(self, fields: Iterable[str], message: str):
        self.fields = fields
        self.message = message

    def __call__(self, attrs: OrderedDict) -> None:
        field_values_set = {attrs[field_name] for field_name in self.fields}

        if len(field_values_set) != 1:
            raise serializers.ValidationError(self.message)


class UniqueWithinCompanyValidator:
    """
    Filters specified queryset by provided serializer field or set of fields
    and validates that within user's company there are no results found.
    """
    
    requires_context = True

    def __init__(self, queryset: Union[QuerySet, Iterable], fields: Iterable[str]):
        self.queryset = queryset
        self.fields = fields

    def exclude_current_instance(self, queryset: Union[QuerySet, Iterable],
                                 instance: Model) -> Union[QuerySet, Iterable]:
        if instance is not None:
            return queryset.exclude(pk=instance.pk)
        return queryset

    def __call__(self, attrs: OrderedDict, serializer: Serializer) -> None:
        filter_fields = {field_name: attrs[field_name]
                         for field_name in self.fields}

        queryset = self.queryset
        queryset = self.exclude_current_instance(queryset, serializer.instance)
        company_id = serializer.context['request'].user.company_id

        try:
            queryset.get(**filter_fields, company_id=company_id)
            message = (
                'The fields '
                + ', '.join((*self.fields, 'company'))
                + ' must make a unique set.'
            )
            raise serializers.ValidationError(message)
        except ObjectDoesNotExist:
            pass


class UniqueTogetherWithNestedSerializerValidator:
    """
    "Unpacks" nested serializer fields and combines it
    with top level serializer fields to check for uniqueness
    """
    
    requires_context = True

    def __init__(self, queryset: Union[QuerySet, Iterable],
                 fields: Iterable[str],
                 nested_serializer_field: str,
                 nested_serializer_model: Model):
        self.queryset = queryset
        self.fields = fields
        self.nested_serializer_field = nested_serializer_field
        self.nested_serializer_model = nested_serializer_model

    def exclude_current_instance(self, queryset: Union[QuerySet, Iterable],
                                 instance: Model) -> Union[QuerySet, Iterable]:
        if instance is not None:
            return queryset.exclude(pk=instance.pk)
        return queryset

    def __call__(self, attrs: OrderedDict, serializer: Serializer) -> None:
        filter_fields = {field_name: attrs[field_name]
                         for field_name in self.fields}

        related_model_instance = self.nested_serializer_model.objects.filter(
            **attrs[self.nested_serializer_field])

        filter_fields[self.nested_serializer_field] = (related_model_instance[0]
                                                       if related_model_instance
                                                       else None)
        queryset = self.queryset
        queryset = self.exclude_current_instance(queryset, serializer.instance)

        try:
            queryset.get(**filter_fields)
            message = (
                'The fields '
                + ', '.join((*self.fields, self.nested_serializer_field))
                + ' must make a unique set.'
            )
            raise serializers.ValidationError(message)
        except ObjectDoesNotExist:
            pass
