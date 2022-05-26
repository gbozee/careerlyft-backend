# Generated by Django 2.0.7 on 2018-11-29 22:10

from django.conf import settings
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('authentication_service', '0011_user_dob'),
    ]

    operations = [
        migrations.CreateModel(
            name='Plan',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('data', django.contrib.postgres.fields.jsonb.JSONField(default={'amount': {'quarterly': {'eur': 24.95, 'ghs': 100, 'gbp': 24.95, 'kes': 1500, 'ngn': 3500, 'usd': 24.95, 'zar': 300}, 'semi_annual': {'eur': 40, 'ghs': 180, 'gbp': 40, 'kes': 2500, 'ngn': 6000, 'usd': 40, 'zar': 500}}, 'discount': 20})),
                ('resume_allowed', models.IntegerField(default=1, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='UserPlan',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('currency', models.CharField(blank=True, max_length=100, null=True)),
                ('duration', models.CharField(blank=True, choices=[('quarterly', 'quarterly'), ('semi_annual', 'semi_annual'), ('annual', 'annual')], max_length=100, null=True)),
                ('expiry_date', models.DateTimeField(blank=True, null=True)),
                ('last_renewed', models.DateTimeField(blank=True, null=True)),
                ('plan', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='users', to='authentication_service.Plan')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='plan', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]