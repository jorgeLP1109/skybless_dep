# Generated by Django 5.1.3 on 2025-02-21 19:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0023_alter_codigogiftcard_codigo_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='compra',
            name='codigos_giftcard',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
