# Generated by Django 3.2.13 on 2023-03-21 15:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='historicaluser',
            name='agreed_to_terms',
        ),
        migrations.RemoveField(
            model_name='user',
            name='agreed_to_terms',
        ),
    ]
