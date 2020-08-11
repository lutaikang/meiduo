from django.db import models


class BaseModel(models.Model):
    """为模型类补充字段"""

    ctime = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    mtime = models.DateTimeField(auto_now=True, verbose_name='修改时间')

    class Meta:
        abstract = True  # 说明是抽象类，迁移时不创建数据表
