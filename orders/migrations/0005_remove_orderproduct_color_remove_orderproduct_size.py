# Generated by Django 4.2.6 on 2023-12-17 18:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_order_address'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderproduct',
            name='color',
        ),
        migrations.RemoveField(
            model_name='orderproduct',
            name='size',
        ),
    ]
