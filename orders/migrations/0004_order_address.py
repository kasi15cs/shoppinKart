# Generated by Django 4.2.6 on 2023-12-16 04:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('address', '0002_address_is_active'),
        ('orders', '0003_remove_order_address_line_1_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='address',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='address.address'),
        ),
    ]