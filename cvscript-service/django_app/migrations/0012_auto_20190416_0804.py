# Generated by Django 2.0.7 on 2019-04-16 07:04

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_app', '0011_auto_20180526_1300'),
    ]

    operations = [
        migrations.CreateModel(
            name='Miscellaneous',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kind', models.CharField(choices=[('project', 'project'), ('jobs', 'jobs')], max_length=15)),
                ('details', django.contrib.postgres.fields.jsonb.JSONField(blank=True)),
            ],
        ),
        migrations.AlterField(
            model_name='companyandschool',
            name='kind',
            field=models.IntegerField(choices=[(1, 'Schools'), (2, 'Companies'), (3, 'Courses'), (4, 'Degrees'), (5, 'Job Positions'), (6, 'Softwares'), (7, 'Certification'), (8, 'Affiliations')]),
        ),
        migrations.AlterField(
            model_name='missingrecord',
            name='kind',
            field=models.IntegerField(choices=[(1, 'Schools'), (2, 'Companies'), (3, 'Courses'), (4, 'Degrees'), (5, 'Job Positions'), (6, 'Softwares'), (7, 'Certification'), (8, 'Affiliations')]),
        ),
    ]