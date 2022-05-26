# Generated by Django 2.0.2 on 2018-03-07 10:50

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_app', '0002_auto_20180307_1027'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobcvscript',
            name='level',
            field=models.CharField(db_index=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='jobposition',
            name='industry_skills',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, max_length=200), null=True, size=None),
        ),
        migrations.AlterField(
            model_name='jobposition',
            name='keywords',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, max_length=200), null=True, size=None),
        ),
        migrations.AlterField(
            model_name='jobposition',
            name='name',
            field=models.CharField(db_index=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='jobposition',
            name='software_skills',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, max_length=200), null=True, size=None),
        ),
    ]