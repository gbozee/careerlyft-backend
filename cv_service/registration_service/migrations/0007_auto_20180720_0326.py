# Generated by Django 2.0.7 on 2018-07-20 02:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration_service', '0006_cvprofile_level'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cvprofile',
            name='user_id',
            field=models.IntegerField(null=True),
        ),
    ]
