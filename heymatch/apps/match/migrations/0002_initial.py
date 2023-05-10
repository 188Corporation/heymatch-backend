# Generated by Django 3.2.13 on 2023-05-10 16:15

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('match', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('group', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalmatchrequest',
            name='history_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicalmatchrequest',
            name='receiver_group',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='group.groupv2'),
        ),
        migrations.AddField(
            model_name='historicalmatchrequest',
            name='sender_group',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='group.groupv2'),
        ),
    ]
