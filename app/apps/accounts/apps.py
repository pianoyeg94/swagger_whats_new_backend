import enum

from django.db import connection
from django.apps import AppConfig

from utils.descriptors import EnumAttrValuesSum, EnumAttrValueCombinations


class AccountsConfig(AppConfig):
    name = 'apps.accounts'

    def ready(self) -> None:
        import apps.accounts.signals
        
        company_membership_model = self.get_model('CompanyMembership')
        company_permissions_model = self.get_model('CompanyMembershipPermissions')

        db_tables = connection.introspection.table_names()
        table_name = company_permissions_model._meta.db_table
        
        # if "company_permissions_model" is not yet migrated to the database,
        # return abroptly
        if table_name not in db_tables:
            return
        
        # load company membership permissions from the database (singleton model)
        company_permissions = company_permissions_model.load()
        
        # transform company membership permissions from model instance into enum
        class CompanyMembershipPermissionsEnum(enum.Enum):
            REGISTER_VCS_ACCOUNTS = company_permissions.register_vcs_account
            CREATE_SWAGGER_PROJECTS = company_permissions.create_swagger_projects
            INVITE_NEW_USERS = company_permissions.invite_new_users

            all_permissions = EnumAttrValuesSum()
            all_possible_permission_combinations = EnumAttrValueCombinations()
        
        # assign enum to "company_membership_model" class constant
        company_membership_model.PERMISSIONS_ENUM = CompanyMembershipPermissionsEnum
