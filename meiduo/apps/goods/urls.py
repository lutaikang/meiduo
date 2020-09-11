from django.urls import path, re_path

from .models import GoodsVisitCount
from .views import ListView, HotGoodsView, GoodsDetailView, DetailVisitView, UserBrowseHistory

urlpatterns = [
    re_path(r'^list/(?P<category_id>\d+)/(?P<page_num>\d+)/$', ListView.as_view(), name='list'),
    re_path(r'^hot/(?P<category_id>\d+)/$', HotGoodsView.as_view(), name='hot'),
    re_path(r'^detail/(?P<sku_id>\d+)/$', GoodsDetailView.as_view(), name='detail'),
    re_path(r'^detail/visit/(?P<category_id>\d+)/$', DetailVisitView.as_view(), name='visit'),
    re_path(r'^browse_histories/$', UserBrowseHistory.as_view()),
]
