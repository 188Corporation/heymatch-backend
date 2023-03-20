# Generated by Django 3.2.13 on 2023-03-20 13:45

import birthday.fields
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager
import django.utils.timezone
import heymatch.apps.user.models
import phonenumber_field.modelfields
import simple_history.models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('hotplace', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('stream_token', models.TextField()),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_first_signup', models.BooleanField(default=True)),
                ('username', models.CharField(default=heymatch.apps.user.models.generate_random_username, max_length=10, unique=True)),
                ('phone_number', phonenumber_field.modelfields.PhoneNumberField(blank=True, max_length=128, null=True, region=None)),
                ('gender', models.CharField(blank=True, choices=[('m', 'Male'), ('f', 'Female')], default=None, max_length=1, null=True)),
                ('birthdate_dayofyear_internal', models.PositiveSmallIntegerField(default=None, editable=False, null=True)),
                ('birthdate', birthday.fields.BirthdayField(blank=True, default=None, null=True)),
                ('height_cm', models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(125), django.core.validators.MaxValueValidator(210)])),
                ('male_body_form', models.CharField(blank=True, choices=[('thin', 'Thin'), ('slender', 'Slender'), ('normal', 'Normal'), ('chubby', 'Chubby'), ('muscular', 'Muscular'), ('bulky', 'Bulky')], max_length=15, null=True)),
                ('female_body_form', models.CharField(blank=True, choices=[('thin', 'Thin'), ('slender', 'Slender'), ('normal', 'Normal'), ('chubby', 'Chubby'), ('glamorous', 'Glamorous'), ('bulky', 'Bulky')], max_length=15, null=True)),
                ('job_title', models.CharField(blank=True, choices=[('college_student', 'College Student'), ('employee', 'Employee'), ('self_employed', 'Self Employed'), ('part_time', 'Part Time'), ('businessman', 'Businessman'), ('etc', 'Etc')], default=None, max_length=32, null=True)),
                ('verified_school_name', models.CharField(blank=True, default=None, max_length=32, null=True)),
                ('verified_company_name', models.CharField(blank=True, default=None, max_length=32, null=True)),
                ('point_balance', models.IntegerField(default=10)),
                ('free_pass', models.BooleanField(default=False)),
                ('free_pass_active_until', models.DateTimeField(blank=True, default=heymatch.apps.user.models.free_pass_default_time, null=True)),
                ('is_temp_user', models.BooleanField(default=False)),
                ('is_deleted', models.BooleanField(default=False)),
                ('agreed_to_terms', models.BooleanField(default=False)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AppInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('faq_url', models.URLField()),
                ('terms_of_service_url', models.URLField()),
                ('privacy_policy_url', models.URLField()),
                ('terms_of_location_service_url', models.URLField()),
                ('business_registration_url', models.URLField()),
            ],
        ),
        migrations.CreateModel(
            name='UserProfileImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveIntegerField(db_index=True, editable=False, verbose_name='order')),
                ('is_main', models.BooleanField(default=False)),
                ('status', models.CharField(blank=True, choices=[('n', 'Not Verified'), ('u', 'Under Verification'), ('a', 'Accepted'), ('r', 'Rejected')], default='n', max_length=1, null=True)),
                ('image', models.ImageField(upload_to=heymatch.apps.user.models.upload_to)),
                ('image_blurred', models.ImageField(upload_to=heymatch.apps.user.models.upload_to)),
                ('thumbnail', models.ImageField(upload_to=heymatch.apps.user.models.upload_to)),
                ('thumbnail_blurred', models.ImageField(upload_to=heymatch.apps.user.models.upload_to)),
                ('is_active', models.BooleanField(default=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='user_profile_images', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
            managers=[
                ('active_objects', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='HistoricalUserProfileImage',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('order', models.PositiveIntegerField(db_index=True, editable=False, verbose_name='order')),
                ('is_main', models.BooleanField(default=False)),
                ('status', models.CharField(blank=True, choices=[('n', 'Not Verified'), ('u', 'Under Verification'), ('a', 'Accepted'), ('r', 'Rejected')], default='n', max_length=1, null=True)),
                ('image', models.TextField(max_length=100)),
                ('image_blurred', models.TextField(max_length=100)),
                ('thumbnail', models.TextField(max_length=100)),
                ('thumbnail_blurred', models.TextField(max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical user profile image',
                'verbose_name_plural': 'historical user profile images',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalUser',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('stream_token', models.TextField()),
                ('id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False)),
                ('is_first_signup', models.BooleanField(default=True)),
                ('username', models.CharField(db_index=True, default=heymatch.apps.user.models.generate_random_username, max_length=10)),
                ('phone_number', phonenumber_field.modelfields.PhoneNumberField(blank=True, max_length=128, null=True, region=None)),
                ('gender', models.CharField(blank=True, choices=[('m', 'Male'), ('f', 'Female')], default=None, max_length=1, null=True)),
                ('birthdate_dayofyear_internal', models.PositiveSmallIntegerField(default=None, editable=False, null=True)),
                ('birthdate', birthday.fields.BirthdayField(blank=True, default=None, null=True)),
                ('height_cm', models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(125), django.core.validators.MaxValueValidator(210)])),
                ('male_body_form', models.CharField(blank=True, choices=[('thin', 'Thin'), ('slender', 'Slender'), ('normal', 'Normal'), ('chubby', 'Chubby'), ('muscular', 'Muscular'), ('bulky', 'Bulky')], max_length=15, null=True)),
                ('female_body_form', models.CharField(blank=True, choices=[('thin', 'Thin'), ('slender', 'Slender'), ('normal', 'Normal'), ('chubby', 'Chubby'), ('glamorous', 'Glamorous'), ('bulky', 'Bulky')], max_length=15, null=True)),
                ('job_title', models.CharField(blank=True, choices=[('college_student', 'College Student'), ('employee', 'Employee'), ('self_employed', 'Self Employed'), ('part_time', 'Part Time'), ('businessman', 'Businessman'), ('etc', 'Etc')], default=None, max_length=32, null=True)),
                ('verified_school_name', models.CharField(blank=True, default=None, max_length=32, null=True)),
                ('verified_company_name', models.CharField(blank=True, default=None, max_length=32, null=True)),
                ('point_balance', models.IntegerField(default=10)),
                ('free_pass', models.BooleanField(default=False)),
                ('free_pass_active_until', models.DateTimeField(blank=True, default=heymatch.apps.user.models.free_pass_default_time, null=True)),
                ('is_temp_user', models.BooleanField(default=False)),
                ('is_deleted', models.BooleanField(default=False)),
                ('agreed_to_terms', models.BooleanField(default=False)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical user',
                'verbose_name_plural': 'historical users',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='FakeChatUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('target_hotplace', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='fake_chat_user_hotplace', to='hotplace.hotplace')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='fake_chat_user', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='EmailVerificationCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254)),
                ('type', models.CharField(choices=[('school', 'School'), ('company', 'Company')], max_length=15)),
                ('code', models.CharField(default=heymatch.apps.user.models.auto_generate_email_verification_code, max_length=5)),
                ('active_until', models.DateTimeField(default=heymatch.apps.user.models.email_verification_code_valid_until)),
                ('is_active', models.BooleanField(default=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='user_email_verification_code', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='DeleteScheduledUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('delete_schedule_at', models.DateTimeField(default=heymatch.apps.user.models.delete_schedule_default_time)),
                ('delete_reason', models.TextField(blank=True, default=None, max_length=500, null=True)),
                ('status', models.CharField(choices=[('WAITING', 'Waiting'), ('COMPLETED', 'Completed'), ('CANCELED', 'Canceled')], default='WAITING', max_length=24)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
