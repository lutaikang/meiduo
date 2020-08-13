import re

from QQLoginTool.QQtool import OAuthQQ
from django.contrib.auth import login
from django.db import DatabaseError
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseServerError
from django.shortcuts import render, redirect
from django.conf import settings
import logging

# Create your views here.
from django.views import View
from django_redis import get_redis_connection

from meiduo.utils.response_code import RETCODE
from oauth.models import OauthQQUser
from oauth.utils import generate_eccess_token, check_access_token
from users.models import User


class QQAuthURLView(View):
    """生成扫码登录链接"""

    def get(self, request):
        # next表示从那个页面进入到登录页面，将来登录成功后就自动回到那个页面
        _next = request.GET.get('next')

        # 获取qq登录页面网址
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI, state=_next)
        login_url = oauth.get_qq_url()
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'login_url': login_url})


class QQAuthUserView(View):
    """用户登陆回调处理"""

    def get(self, request):
        code = request.GET.get('code')
        _next = request.GET.get('state')

        if not all([code, _next]):
            return HttpResponseForbidden('缺少code或state')

        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI)
        try:
            # 通过code去获取token
            access_token = oauth.get_access_token(code=code)
            openid = oauth.get_open_id(access_token)
        except Exception as e:
            # logger.error(e)
            return HttpResponseServerError('OAuth2.0认证失败')

        # 判断该QQ账号是不是第一次登录
        try:
            oauth_user = OauthQQUser.objects.get(openid=openid)
        except OauthQQUser.DoesNotExist:
            # 如果是第一次登录，则绑定手机号
            access_token = generate_eccess_token(openid)
            context = {'access_token_openid': access_token}
            return render(request, 'oauth_callback.html', context)
        else:
            # 重定向到next的位置
            user = oauth_user.user
            # 实现状态保持
            login(request, user)
            response = redirect(_next)
            response.set_cookie('username', user.username, max_age=3600 * 24 * 15)

            return response

    def post(self, request):
        """openid 绑定用户"""
        access_token = request.POST.get('access_token_openid')
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        sms_code_client = request.POST.get('sms_code')

        if not all([access_token, mobile, password, sms_code_client]):
            return HttpResponseForbidden('缺少必传参数')

        # 判断手机号是否合法
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseForbidden('请输入正确的手机号码')
        # 判断密码是否合格
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return HttpResponseForbidden('请输入8-20位的密码')
        # 判断短信验证码是否一致
        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get('sms_%s' % mobile)

        redis_conn.delete('sms_%s' % mobile)
        redis_conn.delete('send_flag_%s' % mobile)

        if sms_code_server is None:
            return render(request, 'oauth_callback.html', {'sms_code_errmsg': '无效的短信验证码'})
        if sms_code_client != sms_code_server.decode():
            return render(request, 'oauth_callback.html', {'sms_code_errmsg': '输入短信验证码有误'})
        # 判断openid是否有效：错误提示放在sms_code_errmsg位置
        openid = check_access_token(access_token)
        if not openid:
            return render(request, 'oauth_callback.html', {'openid_errmsg': '无效的openid'})

        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            user = User.objects.create(username=mobile, password=password, mobile=mobile)
        else:
            # 如果用户存在，则检查密码
            # 如果用户存在，检查用户密码
            if not user.check_password(password):
                return render(request, 'oauth_callback.html', {'account_errmsg': '用户名或密码错误'})

        # 将用户绑定openid
        try:
            OauthQQUser.objects.create(openid=openid, user=user)
        except DatabaseError:
            return render(request, 'oauth_callback.html', {'qq_login_errmsg': 'QQ登录失败'})

        # 实现状态保持
        login(request, user)

        # 响应绑定结果
        _next = request.GET.get('state')
        response = redirect(_next)

        # 登录时用户名写入到cookie，有效期15天
        response.set_cookie('username', user.username, max_age=3600 * 24 * 15)
        return response