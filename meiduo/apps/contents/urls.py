from django.urls import path

from contents import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index')
]
