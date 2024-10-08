# Generated by Django 3.2.13 on 2023-07-07 04:40

import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.utils.timezone
import heymatch.apps.group.models
import simple_history.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gps_geoinfo', heymatch.apps.group.models.EncryptedGeoLocationField(max_length=100)),
                ('title', models.CharField(max_length=100)),
                ('introduction', models.TextField(max_length=500)),
                ('male_member_number', models.IntegerField(blank=True, null=True)),
                ('female_member_number', models.IntegerField(blank=True, null=True)),
                ('member_average_age', models.IntegerField(blank=True, null=True)),
                ('match_point', models.IntegerField(default=1)),
                ('is_active', models.BooleanField(default=True)),
                ('is_deleted', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='GroupMember',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_user_leader', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='GroupProfileImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveIntegerField(db_index=True, editable=False, verbose_name='order')),
                ('image', models.ImageField(upload_to=heymatch.apps.group.models.upload_to)),
                ('image_blurred', models.ImageField(upload_to=heymatch.apps.group.models.upload_to)),
                ('thumbnail', models.ImageField(upload_to=heymatch.apps.group.models.upload_to)),
                ('thumbnail_blurred', models.ImageField(upload_to=heymatch.apps.group.models.upload_to)),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GroupProfilePhotoPurchased',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='GroupV2',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mode', models.CharField(choices=[('simple', 'Simple'), ('invite', 'Invite')], max_length=10)),
                ('title', models.CharField(max_length=100)),
                ('introduction', models.TextField(max_length=500)),
                ('meetup_date', models.DateField()),
                ('meetup_timerange', models.CharField(blank=True, choices=[('lunch', 'Lunch'), ('afternoon', 'Afternoon'), ('dinner', 'Dinner'), ('night', 'Night'), ('not_sure', 'Not Sure')], max_length=20, null=True)),
                ('meetup_place_title', models.CharField(max_length=250)),
                ('meetup_place_address', models.CharField(max_length=250)),
                ('gps_point', django.contrib.gis.db.models.fields.PointField(geography=True, srid=4326)),
                ('gps_address', models.CharField(max_length=250)),
                ('member_number', models.IntegerField(blank=True, null=True)),
                ('member_avg_age', models.IntegerField(blank=True, null=True)),
                ('photo_point', models.IntegerField(default=1)),
                ('match_point', models.IntegerField(default=3)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='HistoricalGroup',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('gps_geoinfo', heymatch.apps.group.models.EncryptedGeoLocationField(max_length=100)),
                ('title', models.CharField(max_length=100)),
                ('introduction', models.TextField(max_length=500)),
                ('male_member_number', models.IntegerField(blank=True, null=True)),
                ('female_member_number', models.IntegerField(blank=True, null=True)),
                ('member_average_age', models.IntegerField(blank=True, null=True)),
                ('match_point', models.IntegerField(default=1)),
                ('is_active', models.BooleanField(default=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
            ],
            options={
                'verbose_name': 'historical group',
                'verbose_name_plural': 'historical groups',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalGroupMember',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('is_user_leader', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
            ],
            options={
                'verbose_name': 'historical group member',
                'verbose_name_plural': 'historical group members',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalGroupProfileImage',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('order', models.PositiveIntegerField(db_index=True, editable=False, verbose_name='order')),
                ('image', models.TextField(max_length=100)),
                ('image_blurred', models.TextField(max_length=100)),
                ('thumbnail', models.TextField(max_length=100)),
                ('thumbnail_blurred', models.TextField(max_length=100)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
            ],
            options={
                'verbose_name': 'historical group profile image',
                'verbose_name_plural': 'historical group profile images',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalGroupProfilePhotoPurchased',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
            ],
            options={
                'verbose_name': 'historical group profile photo purchased',
                'verbose_name_plural': 'historical group profile photo purchaseds',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalGroupV2',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('mode', models.CharField(choices=[('simple', 'Simple'), ('invite', 'Invite')], max_length=10)),
                ('title', models.CharField(max_length=100)),
                ('introduction', models.TextField(max_length=500)),
                ('meetup_date', models.DateField()),
                ('meetup_timerange', models.CharField(blank=True, choices=[('lunch', 'Lunch'), ('afternoon', 'Afternoon'), ('dinner', 'Dinner'), ('night', 'Night'), ('not_sure', 'Not Sure')], max_length=20, null=True)),
                ('meetup_place_title', models.CharField(max_length=250)),
                ('meetup_place_address', models.CharField(max_length=250)),
                ('gps_point', django.contrib.gis.db.models.fields.PointField(geography=True, srid=4326)),
                ('gps_address', models.CharField(max_length=250)),
                ('member_number', models.IntegerField(blank=True, null=True)),
                ('member_avg_age', models.IntegerField(blank=True, null=True)),
                ('photo_point', models.IntegerField(default=1)),
                ('match_point', models.IntegerField(default=3)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('is_active', models.BooleanField(default=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
            ],
            options={
                'verbose_name': 'historical group v2',
                'verbose_name_plural': 'historical group v2s',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='Recent24HrTopGroupAddress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('result', models.JSONField(default=dict)),
                ('aggregated_at', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
            ],
        ),
        migrations.CreateModel(
            name='ReportedGroupV2',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reported_reason', models.TextField(blank=True, max_length=500, null=True)),
                ('status', models.CharField(choices=[('REPORTED', 'Reported'), ('UNDER_REVIEW', 'Under Review'), ('PROCESSED', 'Processed')], default='REPORTED', max_length=32)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
    ]
