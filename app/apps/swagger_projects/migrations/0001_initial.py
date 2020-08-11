from django.conf import settings
import django.contrib.postgres.fields.jsonb
import django.contrib.postgres.indexes
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RemoteVCSAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account_name', models.CharField(max_length=150, verbose_name='Remote VCS Account Name')),
                ('access_token', models.CharField(max_length=300, verbose_name='Remote VCS Account OAuth Access Token')),
                ('refresh_token', models.CharField(default=None, max_length=300, null=True, verbose_name='Remote VCS Account OAuth Refresh Token')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('remote_vcs_service', models.CharField(choices=[('GH', 'GitHub'), ('BB', 'Bitbucket')], max_length=2, verbose_name='Remote VCS Service Provider')),
                ('account_type', models.CharField(choices=[('U', 'User'), ('O', 'Organization')], max_length=1, verbose_name='Remote VCS Account Type')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='remote_vcs_accounts', to='accounts.Company', verbose_name='Owned by Company')),
            ],
            options={
                'db_table': 'remote_vcs_accounts',
            },
        ),
        migrations.CreateModel(
            name='SwaggerFileChange',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('related_commit_details', django.contrib.postgres.fields.jsonb.JSONField(default=list, verbose_name='Commits that presumably triggered this Swagger File Change')),
                ('swagger_file_changes', django.contrib.postgres.fields.jsonb.JSONField(default=dict, verbose_name='Swagger File Change Details')),
                ('changes_added_at', models.DateTimeField(db_index=True, default=None, null=True, verbose_name='Swagger File Changes Added At')),
            ],
            options={
                'db_table': 'swagger_file_changes',
            },
        ),
        migrations.CreateModel(
            name='SwaggerProject',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('project_name', models.CharField(max_length=150, verbose_name='Swagger Project Name')),
                ('use_vcs', models.BooleanField(default=True, verbose_name='Swagger Project Uses a VCS Account')),
                ('remote_repo_name', models.CharField(default=None, max_length=150, null=True, verbose_name='Remote VCS Repository Name')),
                ('remote_repo_branch', models.CharField(default=None, max_length=150, null=True, verbose_name='Remote VCS Repository Branch')),
                ('swagger_file_url', models.URLField(max_length=300, verbose_name='Swagger File URL')),
                ('webhook_id', models.CharField(default=None, max_length=300, null=True, verbose_name='Remote VCS Repository Webhook ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='swagger_projects', to='accounts.Company', verbose_name='Owned by Company')),
                ('project_owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='swagger_projects', to=settings.AUTH_USER_MODEL, verbose_name='Swagger Project Owner')),
                ('remote_vcs_account', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='swagger_projects', to='swagger_projects.RemoteVCSAccount', verbose_name='Associated Remote VCS Account')),
            ],
            options={
                'db_table': 'swagger_projects',
            },
        ),
        migrations.CreateModel(
            name='SwaggerFileChangeComment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment_text', models.TextField(verbose_name='Comment Text')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('comment_author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='swagger_file_change_comments', to=settings.AUTH_USER_MODEL, verbose_name='Comment Author')),
                ('swagger_file_change', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='swagger_projects.SwaggerFileChange', verbose_name='Associated Swagger File Change')),
            ],
            options={
                'db_table': 'swagger_file_changes_comments',
            },
        ),
        migrations.AddField(
            model_name='swaggerfilechange',
            name='swagger_project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='swagger_file_changes', to='swagger_projects.SwaggerProject', verbose_name='Associated Swagger Project'),
        ),
        migrations.CreateModel(
            name='SwaggerFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('swagger_file', django.contrib.postgres.fields.jsonb.JSONField(verbose_name='Swagger File')),
                ('swagger_project', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='swagger_file', to='swagger_projects.SwaggerProject', verbose_name='Associated Swagger Project')),
            ],
            options={
                'db_table': 'swagger_files',
            },
        ),
        migrations.AddIndex(
            model_name='swaggerproject',
            index=models.Index(fields=['created_at', 'company'], name='idx_swg_prj_created_at'),
        ),
        migrations.AddIndex(
            model_name='swaggerproject',
            index=django.contrib.postgres.indexes.GinIndex(fields=['remote_repo_name', 'company'], name='idx_swg_prj_remote_repo_name'),
        ),
        migrations.AddIndex(
            model_name='swaggerproject',
            index=django.contrib.postgres.indexes.GinIndex(fields=['remote_repo_branch', 'company'], name='idx_swg_prj_remote_repo_branch'),
        ),
        migrations.AddConstraint(
            model_name='swaggerproject',
            constraint=models.UniqueConstraint(fields=('remote_vcs_account', 'remote_repo_name', 'remote_repo_branch'), name='unique_remote_repo_branch'),
        ),
        migrations.AddConstraint(
            model_name='swaggerproject',
            constraint=models.UniqueConstraint(fields=('project_name', 'company'), name='unique_swagger_project_name'),
        ),
        migrations.AddIndex(
            model_name='remotevcsaccount',
            index=models.Index(fields=['created_at', 'company'], name='idx_vcs_accs_created_at'),
        ),
        migrations.AddConstraint(
            model_name='remotevcsaccount',
            constraint=models.UniqueConstraint(fields=('remote_vcs_service', 'company', 'account_name'), name='unique_vcs_account_name'),
        ),
    ]
