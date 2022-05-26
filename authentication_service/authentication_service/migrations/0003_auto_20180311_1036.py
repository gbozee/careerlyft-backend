# Generated by Django 2.0.2 on 2018-03-11 09:36

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("authentication_service", "0002_auto_20180310_1955")]

    operations = [
        migrations.AddField(
            model_name="user",
            name="contact_address",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="country",
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="phone_number",
            field=models.CharField(blank=True, max_length=15, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="photo_url",
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="social",
            field=django.contrib.postgres.fields.jsonb.JSONField(null=True),
        ),
        migrations.AlterField(
            model_name="user",
            name="email",
            field=models.EmailField(
                db_index=True,
                error_messages={"unique": "A user with that username already exists."},
                max_length=254,
                unique=True,
                verbose_name="email address",
            ),
        ),
    ]
