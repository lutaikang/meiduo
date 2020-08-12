from django.contrib.auth.models import AbstractUser, User
from django.db import models


# Create your models here.


class User(AbstractUser):
    """自定义用户模型类"""
    mobile = models.CharField(max_length=11, unique=True, verbose_name='手机号')
    email_active = models.BooleanField(default=False, verbose_name='邮箱验证')

    class Meta:
        db_table = 'tb_user'
        verbose_name = verbose_name_plural = '用户'

    def __str__(self):
        return self.username
