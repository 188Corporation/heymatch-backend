# Generated by Django 3.2.13 on 2023-11-16 14:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0006_auto_20231113_2003'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicaluser',
            name='hide_my_school_or_company_name',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='hide_my_school_or_company_name',
            field=models.BooleanField(default=False),
        ),
    ]
