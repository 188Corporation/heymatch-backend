# Generated by Django 3.2.13 on 2022-05-07 18:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='group',
            name='member_avg_age',
        ),
        migrations.RemoveField(
            model_name='group',
            name='member_number',
        ),
    ]
