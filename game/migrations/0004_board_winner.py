# Generated by Django 3.2.3 on 2021-05-30 01:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0003_board_colorflag'),
    ]

    operations = [
        migrations.AddField(
            model_name='board',
            name='winner',
            field=models.BooleanField(default=False),
        ),
    ]