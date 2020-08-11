import apps.accounts.models.user
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import imagekit.models.fields
from django.contrib.postgres.operations import BtreeGinExtension


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        # for usage with data types that are not supported out of the box
        BtreeGinExtension(),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('email', models.EmailField(max_length=150, unique=True, verbose_name='Email Address')),
                ('first_name', models.CharField(max_length=150, verbose_name='First Name')),
                ('last_name', models.CharField(max_length=150, verbose_name='Last Name')),
                ('email_confirmed', models.BooleanField(default=True, verbose_name='User Comfirmed His Email')),
                ('password_changed_at', models.DateTimeField(default=None, null=True, verbose_name='Password Changed At')),
                ('password_reset_token', models.CharField(default=None, max_length=250, null=True, verbose_name='Password Reset Token')),
                ('password_reset_expires', models.DateTimeField(default=None, null=True, verbose_name='Password Reset Token Expires At')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
            ],
            options={
                'db_table': 'users',
            },
            managers=[
                ('objects', apps.accounts.models.user.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_name', models.CharField(max_length=150, unique=True, verbose_name='Company Name')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
            ],
            options={
                'db_table': 'companies',
            },
        ),
        migrations.CreateModel(
            name='CompanyMembershipPermissions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('register_vcs_account', models.IntegerField(default=1, verbose_name='Company Member is allowed to register New VCS Accounts')),
                ('create_swagger_projects', models.IntegerField(default=2, verbose_name='Company Member is allowed to create New Swagger Projects')),
                ('invite_new_users', models.IntegerField(default=4, verbose_name='Company Member is allowed to invite New Users')),
            ],
            options={
                'db_table': 'company_membership_permissions',
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number', models.CharField(default=None, max_length=15, null=True, verbose_name='Phone Number')),
                ('skype', models.CharField(default=None, max_length=150, null=True, verbose_name='Skype')),
                ('profile_photo', imagekit.models.fields.ProcessedImageField(max_length=300, null=True, upload_to=apps.accounts.models.user.photo_path, verbose_name='Profile Photo')),
                ('profile_owner', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL, verbose_name='User Associated With This Profile')),
            ],
            options={
                'db_table': 'user_profiles',
            },
        ),
        migrations.CreateModel(
            name='CompanyMembership',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('is_company_owner', models.BooleanField(default=False, verbose_name='Company Member owns this Company')),
                ('job_title', models.CharField(max_length=150, verbose_name="Company Member's Job Title")),
                ('permissions', models.IntegerField(default=0, verbose_name='Company Membership Permissions')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='accounts.Company', verbose_name='Company associated with this Membership')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='company_memberships', to=settings.AUTH_USER_MODEL, verbose_name='User associated with this Membership.')),
            ],
            options={
                'db_table': 'company_memberships',
            },
        ),
        migrations.CreateModel(
            name='CompanyInvitation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, verbose_name='Email Address')),
                ('invitation_token', models.CharField(max_length=150, verbose_name='Hashed Company Invitation Token')),
                ('invitation_expires', models.DateTimeField(verbose_name='Company Invitation Token Expires At')),
                ('desired_company_permissions', models.IntegerField(default=0, verbose_name='Preassigned Company Membership Permissions')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invitations', to='accounts.Company', verbose_name='Company associated with this Invitation')),
            ],
            options={
                'db_table': 'company_invitations',
            },
        ),
        migrations.AddField(
            model_name='company',
            name='user',
            field=models.ManyToManyField(related_name='companies', through='accounts.CompanyMembership', to=settings.AUTH_USER_MODEL, verbose_name='Company Member'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['created_at'], name='idx_users_created_at'),
        ),
    ]
