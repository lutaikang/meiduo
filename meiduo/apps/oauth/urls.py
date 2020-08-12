from django.urls import path

from oauth import views

urlpatterns = [
    path('qq/login/', views.QQAuthURLView.as_view(), name='qq'),
    path('oauth_callback/', views.QQAuthUserView.as_view()),
]