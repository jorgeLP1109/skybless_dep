# Generated by Django 5.1.3 on 2025-02-10 22:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0018_alter_codigoenviado_codigo_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='codigoenviado',
            name='Tarjeta',
            field=models.ManyToManyField(to='productos.tarjeta'),
        ),
    ]
