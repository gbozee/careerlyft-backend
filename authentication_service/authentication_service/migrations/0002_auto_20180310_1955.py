# Generated by Django 2.0.2 on 2018-03-10 18:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("authentication_service", "0001_initial")]

    operations = [
        migrations.RemoveField(model_name="userprofile", name="user"),
        migrations.AlterField(
            model_name="user",
            name="email",
            field=models.EmailField(
                error_messages={"unique": "A user with that username already exists."},
                max_length=254,
                unique=True,
                verbose_name="email address",
            ),
        ),
        migrations.AlterField(
            model_name="user", name="last_login", field=models.DateTimeField(null=True)
        ),
        migrations.DeleteModel(name="UserProfile"),
    ]
