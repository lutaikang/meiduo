from django.urls import path, re_path

from verifications import views

urlpatterns = [
    re_path('image_codes/(?P<uuid>[\w-]+)/', views.ImageCodeView.as_view()),  # 验证码图片

]
