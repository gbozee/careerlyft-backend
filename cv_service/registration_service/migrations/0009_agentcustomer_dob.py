# Generated by Django 2.0.7 on 2019-02-12 10:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration_service', '0008_auto_20190208_1616'),
    ]

    operations = [
        migrations.AddField(
            model_name='agentcustomer',
            name='dob',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
