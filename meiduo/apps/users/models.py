from django.contrib.auth.models import AbstractUser, User
from django.db import models

# Create your models here.
from meiduo.utils.models import BaseModel


class User(AbstractUser):
    """自定义用户模型类"""
    mobile = models.CharField(max_length=11, unique=True, verbose_name='手机号')
    email_active = models.BooleanField(default=False, verbose_name='邮箱验证')
    default_address = models.ForeignKey('Address', related_name='users', null=True, blank=True,
                                        on_delete=models.SET_NULL, verbose_name='默认地址')

    class Meta:
        db_table = 'tb_user'
        verbose_name = verbose_name_plural = '用户'

    def __str__(self):
        return self.username


class Address(BaseModel):
    """用户地址"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses', verbose_name='用户')
    title = models.CharField(max_length=20, verbose_name='地址名称')
    receiver = models.CharField(max_length=20, verbose_name='收货人')
    province = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='province_addresses',
                                 verbose_name='省')
    city = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='city_addresses', verbose_name='市')
    district = models.ForeignKey('areas.Area', on_delete=models.PROTECT, related_name='district_addresses',
                                 verbose_name='区/县')
    place = models.CharField(max_length=50, verbose_name='地址')
    mobile = models.CharField(max_length=11, verbose_name='手机号')
    tel = models.CharField(max_length=20, null=True, blank=True, default='', verbose_name='电话')
    email = models.CharField(max_length=30, null=True, blank=True, default='', verbose_name='邮箱')
    is_deleted = models.BooleanField(default=False, verbose_name='逻辑删除')

    class Meta:
        db_table = 'tb_address'
        verbose_name = verbose_name_plural = '用户地址'
        ordering = ['-mtime']
