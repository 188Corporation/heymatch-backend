# Generated by Django 3.2.13 on 2023-03-01 12:19

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0011_auto_20230301_1416'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicaluser',
            name='body_form',
            field=models.CharField(blank=True, choices=[('thin', '마른'), ('slender', '슬림탄탄'), ('normal', '보통'), ('chubby', '통통한'), ('muscular', '근육질의'), ('bulky', '덩치가있는')], max_length=15, null=True),
        ),
        migrations.AddField(
            model_name='historicaluser',
            name='height_cm',
            field=models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(155), django.core.validators.MaxValueValidator(210)]),
        ),
        migrations.AddField(
            model_name='historicaluserprofileimage',
            name='is_main',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='historicaluserprofileimage',
            name='is_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='body_form',
            field=models.CharField(blank=True, choices=[('thin', '마른'), ('slender', '슬림탄탄'), ('normal', '보통'), ('chubby', '통통한'), ('muscular', '근육질의'), ('bulky', '덩치가있는')], max_length=15, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='height_cm',
            field=models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(155), django.core.validators.MaxValueValidator(210)]),
        ),
        migrations.AddField(
            model_name='userprofileimage',
            name='is_main',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userprofileimage',
            name='is_verified',
            field=models.BooleanField(default=False),
        ),
    ]
