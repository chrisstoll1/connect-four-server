# Generated by Django 3.2.3 on 2021-05-29 20:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='board',
            name='redConnected',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='board',
            name='yellowConnected',
            field=models.BooleanField(default=False),
        ),
    ]
