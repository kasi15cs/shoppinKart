# Generated by Django 4.2.6 on 2024-01-03 14:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('category', '0004_category_cat_discount'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='cat_discount',
            field=models.IntegerField(default=0),
        ),
    ]