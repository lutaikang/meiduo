from django.urls import path, re_path
from .views import ListView, HotGoodsView

urlpatterns = [
    re_path(r'^list/(?P<category_id>\d+)/(?P<page_num>\d+)/$', ListView.as_view(), name='list'),
    re_path(r'^hot/(?P<category_id>\d+)/$', HotGoodsView.as_view(), name='hot'),
]
