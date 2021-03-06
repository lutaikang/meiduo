# Generated by Django 3.0.8 on 2020-09-28 02:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ordergoods',
            name='score',
            field=models.SmallIntegerField(choices=[(0, '0分'), (1, '20分'), (2, '40分'), (3, '60分'), (4, '80分'), (5, '100分')], default=5, verbose_name='满意度评分'),
        ),
        migrations.AlterField(
            model_name='orderinfo',
            name='pay_method',
            field=models.SmallIntegerField(choices=[(1, '货到付款'), (2, '支付宝')], default=1, verbose_name='支付方式'),
        ),
        migrations.AlterField(
            model_name='orderinfo',
            name='status',
            field=models.SmallIntegerField(choices=[(1, '待支付'), (2, '待发货'), (3, '待收货'), (4, '待评价'), (5, '已完成'), (6, '已取消')], default=1, verbose_name='订单状态'),
        ),
        migrations.AlterField(
            model_name='orderinfo',
            name='total_amount',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='商品总金额'),
        ),
    ]
