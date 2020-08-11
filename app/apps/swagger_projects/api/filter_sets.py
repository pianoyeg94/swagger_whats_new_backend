from django_filters import rest_framework as filters

from apps.swagger_projects.models import RemoteVCSAccount, SwaggerProject


class RemoteVCSAccountFilter(filters.FilterSet):
    account_name = filters.CharFilter(lookup_expr='icontains')
    remote_vcs_service = filters.ChoiceFilter(
        choices=RemoteVCSAccount.REMOTE_VCS_SERVICE_CHOICES)
    account_type = filters.ChoiceFilter(
        choices=RemoteVCSAccount.ACCOUNT_TYPE_CHOICES)
    
    class Meta:
        model = RemoteVCSAccount
        fields = ('account_name', 'remote_vcs_service', 'account_type')


class SwaggerProjectFilter(filters.FilterSet):
    project_name = filters.CharFilter(lookup_expr='icontains')
    using_vcs = filters.BooleanFilter(field_name='use_vcs')
    remote_repo_name = filters.CharFilter(lookup_expr='icontains')
    remote_repo_branch = filters.CharFilter(lookup_expr='icontains')
    remote_vcs_account_name = filters.CharFilter(
        field_name='remote_vcs_account__account_name',
        lookup_expr='icontains'
    )
    remote_vcs_account_service = filters.ChoiceFilter(
        field_name='remote_vcs_account__remote_vcs_service',
        choices=RemoteVCSAccount.REMOTE_VCS_SERVICE_CHOICES,
    )
    remote_vcs_account_type = filters.ChoiceFilter(
        field_name='remote_vcs_account__account_type',
        choices=RemoteVCSAccount.ACCOUNT_TYPE_CHOICES,
    )
    
    class Meta:
        model = SwaggerProject
        fields = ('project_name', 'using_vcs', 'remote_vcs_account_service',
                  'remote_vcs_account_name', 'remote_vcs_account_type')
