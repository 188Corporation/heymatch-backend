# Generated by Django 3.2.13 on 2022-12-02 14:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0004_auto_20221202_2306'),
        ('match', '0004_auto_20221202_1945'),
    ]

    operations = [
        migrations.AlterField(
            model_name='matchrequest',
            name='receiver_group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='match_request_receiver_group', to='group.group'),
        ),
        migrations.AlterField(
            model_name='matchrequest',
            name='sender_group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='match_request_sender_group', to='group.group'),
        ),
    ]
