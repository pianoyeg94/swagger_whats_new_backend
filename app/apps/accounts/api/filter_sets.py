from django.contrib.auth import get_user_model

from django_filters import rest_framework as filters

User = get_user_model()


class UserFilter(filters.FilterSet):
    first_name = filters.CharFilter(lookup_expr='icontains')
    last_name = filters.CharFilter(lookup_expr='icontains')
    email = filters.CharFilter(lookup_expr='icontains')
    registered = filters.DateFromToRangeFilter(field_name='created_at')
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'registered')
