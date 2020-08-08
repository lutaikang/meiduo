import re

from django.contrib.auth.backends import ModelBackend

from users.models import User


def get_uset_by_account(account):
    """
    根据accout查询用户
    :param account: 用户名或者手机号
    :return:user
    """
    try:
        if re.match(r'^1[3-9]\d{9}', account):
            user = User.objects.get(mobile=account)
        else:
            user = User.objects.get(username=account)
    except User.DoesNotExist:
        return None
    else:
        return user


class UsernameMobileAuthBackend(ModelBackend):
    """自定义认证后端"""

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        重写认证方法，实现多账号登录
        :param request: 请求对象
        :param username: 用户名
        :param password: 密码
        :param kwargs: 其他参数
        :return: user对象
        """
        # 根据传入的username获取user对象.username可以是手机号也可以是账号
        user = get_uset_by_account(username)
        # 校验user是否存在并校验密码是否正确
        if user and user.check_password(password):
            return user

    # def get_user(self, user_id):
    #     try:
    #         if re.match(r'^1[3-9]\d{9}', user_id):
    #             user = User.objects.get(mobile=user_id)
    #         else:
    #             user = User.objects.get(username=user_id)
    #     except User.DoesNotExist:
    #         return None
    #     else:
    #         return user
