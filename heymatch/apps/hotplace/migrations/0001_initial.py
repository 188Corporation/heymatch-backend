# Generated by Django 3.2.13 on 2022-11-09 16:39

import django.contrib.postgres.fields
from django.db import migrations, models
import django_google_maps.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='HotPlace',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32, unique=True, verbose_name='Name of Hotplace')),
                ('zone_center_geoinfo', django_google_maps.fields.GeoLocationField(blank=True, max_length=100, null=True)),
                ('zone_boundary_geoinfos', django.contrib.postgres.fields.ArrayField(base_field=django_google_maps.fields.GeoLocationField(max_length=100), blank=True, null=True, size=None)),
            ],
        ),
    ]
