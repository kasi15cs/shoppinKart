# Generated by Django 4.2.6 on 2024-01-03 19:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0009_orderproduct_product_total_price'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('New', 'New'), ('Accepted', 'Accepted'), ('Completed', 'Completed'), ('failed', 'failed')], default='New', max_length=10),
        ),
    ]
