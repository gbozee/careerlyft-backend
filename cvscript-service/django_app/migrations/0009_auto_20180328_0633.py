# Generated by Django 2.0.3 on 2018-03-28 05:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_app', '0008_auto_20180323_2201'),
    ]

    operations = [
        migrations.CreateModel(
            name='MissingRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=200)),
                ('kind', models.IntegerField(choices=[(1, 'Schools'), (2, 'Companies'), (3, 'Courses'), (4, 'Degrees'), (5, 'Job Positions')])),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterField(
            model_name='companyandschool',
            name='kind',
            field=models.IntegerField(choices=[(1, 'Schools'), (2, 'Companies'), (3, 'Courses'), (4, 'Degrees'), (5, 'Job Positions')]),
        ),
    ]
