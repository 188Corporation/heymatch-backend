# Generated by Django 3.2.13 on 2023-07-07 04:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('chat', '0001_initial'),
        ('group', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='streamchannel',
            name='group_member',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='group.groupmember'),
        ),
    ]
