from django.urls import path

from payment.views import PaymentView, PaymentStatusView

urlpatterns = [
    path('payment/<int:order_id>/', PaymentView.as_view(), name='url'),
    path('payment/status/', PaymentStatusView.as_view()),

]
