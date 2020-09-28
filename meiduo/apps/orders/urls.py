from django.urls import path

from orders.views import OrderSettlementView, OrderCommitView, OrderSuccessView, UserOrderInfoView

urlpatterns = [
    path('orders/settlement/', OrderSettlementView.as_view(), name='settlement'),
    path('orders/commit/', OrderCommitView.as_view(), name='commit'),
    path('orders/success/', OrderSuccessView.as_view(), name='success'),
    path('orders/info/<int:page_num>/', UserOrderInfoView.as_view(), name='info'),
]