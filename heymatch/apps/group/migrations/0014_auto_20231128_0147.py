# Generated by Django 3.2.13 on 2023-11-27 16:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0013_auto_20231126_1632'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupv2',
            name='notified_to_send_mr_after_half_hour',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='groupv2',
            name='notified_to_send_mr_after_one_day',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='groupv2',
            name='notified_to_send_mr_after_three_day',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='historicalgroupv2',
            name='notified_to_send_mr_after_half_hour',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='historicalgroupv2',
            name='notified_to_send_mr_after_one_day',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='historicalgroupv2',
            name='notified_to_send_mr_after_three_day',
            field=models.BooleanField(default=False),
        ),
    ]
