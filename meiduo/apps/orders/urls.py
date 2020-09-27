from django.urls import path

from orders.views import OrderSettlementView, OrderCommitView, OrderSuccessView

urlpatterns = [
    path('orders/settlement/', OrderSettlementView.as_view(), name='settlement'),
    path('orders/commit/', OrderCommitView.as_view(), name='commit'),
    path('orders/success/', OrderSuccessView.as_view(), name='success'),


]