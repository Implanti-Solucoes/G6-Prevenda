# Generated by Django 2.1.1 on 2018-10-20 14:09

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('Financeiro', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='contratos',
            name='id_g6',
            field=models.CharField(default=django.utils.timezone.now, max_length=24, verbose_name='id da movimentacao'),
            preserve_default=False,
        ),
    ]
