import json
import re
from venv import logger

from django.conf import settings
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.db import DatabaseError
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse, HttpResponseServerError
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django_redis import get_redis_connection

from celery_tasks.email.tasks import send_verify_email
from meiduo.utils.response_code import RETCODE
from users.models import User
from users.utils import check_verif_email_token, generate_verify_email_url


class RegisterView(View):

    def get(self, request):
        """
        提供注册页面
        :return:
        :param request: 请求对象
        :return: 注册页面
        """
        return render(request, 'register.html')

    def post(self, request):
        """用户注册"""
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        mobile = request.POST.get('mobile')
        sms_code_client = request.POST.get('sms_code')
        allow = request.POST.get('allow')

        # 对传入数据进行再次校验
        if not all([username, password, password2, mobile, sms_code_client, allow]):
            return HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return HttpResponseForbidden('请输入5-20位字符的名字')
        if not re.match(r'^[0-9A-Za-z]{8,20}', password):
            return HttpResponseForbidden('请输入8-20位的密码')
        if password != password2:
            return HttpResponseForbidden('两次密码输入不一致')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseForbidden('手机格式不正确')
        if allow != 'on':
            return HttpResponseForbidden('请勾选用户协议')

        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get('sms_%s' % mobile)

        try:
            redis_conn.delete('sms_%s' % mobile)
        except Exception as e:
            logger.error(e)

        if sms_code_server is None:
            return render(request, 'register.html', {'sms_code_errmsg': '无效的短信验证码'})
        if sms_code_client != sms_code_server.decode():
            return render(request, 'register.html', {'sms_code_errmsg': '输入短信验证码有误'})

        try:
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
        except DatabaseError:
            return render(request, 'register.html', {'register_errmsg': '注册失败'})

        login(request, user)

        return redirect(reverse('contents:index'))


class UsernameCountView(View):
    """判断用户名是否已经注册"""

    def get(self, requeset, username):
        count = User.objects.filter(username=username).count()
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok', 'count': count})


class UsermobileCountView(View):
    """判断手机号是否重复注册"""

    def get(self, request, mobile):
        count = User.objects.filter(mobile=mobile).count()
        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok', 'count': count})


class LoginView(View):
    """用户登录"""

    def get(self, request):
        """响应用户登录页面"""
        return render(request, 'login.html')

    def post(self, request):
        """用户登录逻辑"""
        username = request.POST.get('username')
        password = request.POST.get('password')
        remembered = request.POST.get('remembered')

        _next = request.GET.get('next')

        if not all([username, password]):
            return HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return HttpResponseForbidden('请输入5-20位字符的名字')
        if not re.match(r'^[a-zA-Z0-9]{8,20}$', password):
            return HttpResponseForbidden('请输入8-20位字符的密码')

        user = authenticate(username=username, password=password)
        if user is None:
            return render(request, 'login.html', context={'account_errmsg': '用户名或密码输入错误'})

        login(request, user)
        # 设置状态保持的周期
        if remembered != 'on':
            request.session.set_expiry(0)
        else:
            request.session.set_expiry(None)

        if _next:
            response = redirect(_next)
        else:
            response = redirect(reverse('contents:index'))
        # 登录时用户名写入到cookie，有效期15天
        response.set_cookie('username', user.username, max_age=3600 * 24 * 15)

        return response


class LogoutView(View):
    """退出登录"""

    def get(self, request):
        """实现退出登录功能"""
        # 清理session
        logout(request)
        # 退出登录重定向到登录页
        response = redirect(reverse('contents:index'))
        response.delete_cookie('username')

        return response


class UserInfo(LoginRequiredMixin, View):
    """用户中心"""

    def get(self, request):
        """提供个人信息页面"""
        user = request.user
        context = {
            'username': user.username,
            'mobile': user.mobile,
            'email': user.email,
            'email_active': user.email_active,
        }

        return render(request, 'user_center_info.html', context)


class EmailView(View):
    """添加邮箱"""

    def put(self, request):
        """实现添加邮箱逻辑"""

        if not request.user.is_authenticated:
            return JsonResponse({'code': RETCODE.SESSIONERR, 'errmsg': '用户未登录'})

        # 接收参数
        json_dict = json.loads(request.body.decode())
        email = json_dict.get('email')

        # 校验参数
        if not email:
            return HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return HttpResponseForbidden('email参数有误')

        try:
            request.user.email = email
            request.user.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '添加邮箱失败'})

        # 异步发送验证邮件
        verify_url = generate_verify_email_url(request.user)
        send_verify_email.delay(email, verify_url)
        # send_mail('1', "", settings.EMAIL_FROM, ['1554284589@qq.com'], '')

        return JsonResponse({'code': RETCODE.OK, 'errmsg': '添加邮箱成功'})

    def get(self, request):
        """验证邮箱接口"""
        token = request.GET.get('token')
        if not token:
            return HttpResponseForbidden('缺少必传参数token')

        user_id, email = check_verif_email_token(token)
        if not user_id and not email:
            return HttpResponseForbidden('无效的token')
        try:
            user = User.objects.get(id=user_id, email=email)
        except User.DoesNotExist:
            return HttpResponseForbidden('无效的token')

        # 修改email_active的值为True
        try:
            user.email_active = True
            user.save()
        except Exception as e:
            return HttpResponseServerError('激活邮箱失败')

        # 返回邮箱验证结果
        return redirect(reverse('users:info'))
