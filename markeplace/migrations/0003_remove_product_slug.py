# Generated by Django 4.1.1 on 2022-10-19 15:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('markeplace', '0002_product_timestamp'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='slug',
        ),
    ]
