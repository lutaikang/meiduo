"""meiduo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

import meiduo_admin

# noinspection SpellCheckingInspection
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(('users.urls', 'users'), namespace='users')),
    path('', include(('contents.urls', 'contents'), namespace='contents')),
    path('', include(('verifications.urls', 'verifications'), namespace='verifications')),
    path('', include(('oauth.urls', 'oauth'), namespace='oauth')),
    path('', include(('areas.urls', 'areas'), namespace='areas')),
    path('', include(('goods.urls', 'goods'), namespace='goods')),
    path('', include(('carts.urls', 'carts'), namespace='carts')),
    path('', include(('orders.urls', 'orders'), namespace='orders')),
    path('', include(('payment.urls', 'payment'), namespace='payment')),
    path(r'search/', include('haystack.urls')),

    path(r'', include(('meiduo_admin.urls', 'meiduo_admin'), namespace='meiduo_admin'))
]
