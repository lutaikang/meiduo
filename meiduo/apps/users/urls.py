from django.urls import path, re_path

from users import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),  # 用户注册
    path('login/', views.LoginView.as_view(), name='login'),  # 用户登录
    path('logout/', views.LogoutView.as_view(), name='logout'),  # 退出登录
    re_path(r'usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/', views.UsernameCountView.as_view(), name='username'),
    re_path(r'mobiles/(?P<mobile>1[3-9]\d{9})/count/', views.UsermobileCountView.as_view(), name='mobile'),  # 校验手机号

    path('userinfo/', views.UserInfo.as_view(), name='info'),  # 用户中心展示
    path('emails/', views.EmailView.as_view()),
    path('emails/verification/', views.EmailView.as_view()),
]
