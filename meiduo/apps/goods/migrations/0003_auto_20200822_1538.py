# Generated by Django 3.0.8 on 2020-08-22 07:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('goods', '0002_auto_20200821_1825'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sku',
            name='default_image',
            field=models.ImageField(blank=True, default='', max_length=200, null=True, upload_to='', verbose_name='默认图片'),
        ),
    ]
