# Generated by Django 3.2.13 on 2022-12-02 14:06

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('payment', '0004_auto_20221130_1616'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userpointconsumptionhistory',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='user_point_consumption_history', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='userpurchase',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='user_purchases', to=settings.AUTH_USER_MODEL),
        ),
    ]
