# Generated by Django 3.2.13 on 2023-03-20 13:45

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('payment', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='userpurchase',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='user_purchases', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='userpointconsumptionhistory',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='user_point_consumption_history', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicaluserpurchase',
            name='apple_store_receipt',
            field=models.ForeignKey(blank=True, db_constraint=False, default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='payment.applestorevalidatedreceipt'),
        ),
        migrations.AddField(
            model_name='historicaluserpurchase',
            name='free_pass_item',
            field=models.ForeignKey(blank=True, db_constraint=False, default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='payment.freepassitem'),
        ),
        migrations.AddField(
            model_name='historicaluserpurchase',
            name='history_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicaluserpurchase',
            name='play_store_receipt',
            field=models.ForeignKey(blank=True, db_constraint=False, default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='payment.playstorevalidatedreceipt'),
        ),
        migrations.AddField(
            model_name='historicaluserpurchase',
            name='point_item',
            field=models.ForeignKey(blank=True, db_constraint=False, default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='payment.pointitem'),
        ),
        migrations.AddField(
            model_name='historicaluserpurchase',
            name='user',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
    ]
