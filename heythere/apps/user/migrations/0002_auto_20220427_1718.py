# Generated by Django 3.2.13 on 2022-04-27 17:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0002_group_title'),
        ('user', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_group_leader',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='joined_group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='group.group'),
        ),
    ]
