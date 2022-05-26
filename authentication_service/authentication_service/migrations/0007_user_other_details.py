# Generated by Django 2.0.3 on 2018-04-17 22:15

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("authentication_service", "0006_user_shared_networks")]

    operations = [
        migrations.AddField(
            model_name="user",
            name="other_details",
            field=django.contrib.postgres.fields.jsonb.JSONField(default={}),
        )
    ]