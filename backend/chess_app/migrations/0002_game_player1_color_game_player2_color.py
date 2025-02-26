# Generated by Django 5.1.6 on 2025-02-26 16:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chess_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='player1_color',
            field=models.CharField(default='white', max_length=10),
        ),
        migrations.AddField(
            model_name='game',
            name='player2_color',
            field=models.CharField(default='black', max_length=10),
        ),
    ]
