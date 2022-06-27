# Generated by Django 3.2.13 on 2022-06-27 14:26

import django.db.models.deletion
from django.db import migrations, models

import heythere.apps.group.models


class Migration(migrations.Migration):
    dependencies = [
        ('group', '0003_groupblacklist'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupprofileimage',
            name='image_blurred',
            field=models.ImageField(default=None, upload_to=heythere.apps.group.models.upload_to),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='groupprofileimage',
            name='thumbnail',
            field=models.ImageField(default=None, upload_to=heythere.apps.group.models.upload_to),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='groupprofileimage',
            name='thumbnail_blurred',
            field=models.ImageField(default=None, upload_to=heythere.apps.group.models.upload_to),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='groupprofileimage',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    to='group.group'),
        ),
    ]
