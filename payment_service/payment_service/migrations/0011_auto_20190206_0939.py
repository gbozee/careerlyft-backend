# Generated by Django 2.0.7 on 2019-02-06 08:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment_service', '0010_auto_20181130_1754'),
    ]

    operations = [
        migrations.AddField(
            model_name='planpayment',
            name='kind',
            field=models.CharField(choices=[('client', 'client'), ('agent', 'agent')], default='client', max_length=50),
        ),
        migrations.AlterField(
            model_name='planpayment',
            name='duration',
            field=models.CharField(blank=True, choices=[('quarterly', 'quarterly'), ('semi_annual', 'semi_annual'), ('annual', 'annual'), ('monthly', 'monthly'), ('annually', 'annually')], max_length=100, null=True),
        ),
    ]
