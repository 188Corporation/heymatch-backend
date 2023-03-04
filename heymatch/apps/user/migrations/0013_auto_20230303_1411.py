# Generated by Django 3.2.13 on 2023-03-03 05:11

import birthday.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0012_auto_20230301_2119'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicaluser',
            name='is_first_signup',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='user',
            name='is_first_signup',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='historicaluser',
            name='birthdate',
            field=birthday.fields.BirthdayField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='historicaluser',
            name='gender',
            field=models.CharField(blank=True, choices=[('m', 'Male'), ('f', 'Female'), ('o', 'Other')], default=None, max_length=1, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='birthdate',
            field=birthday.fields.BirthdayField(blank=True, default=None, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='gender',
            field=models.CharField(blank=True, choices=[('m', 'Male'), ('f', 'Female'), ('o', 'Other')], default=None, max_length=1, null=True),
        ),
    ]
