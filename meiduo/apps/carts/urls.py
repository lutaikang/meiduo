from django.urls import path

from carts.views import CartsView

urlpatterns = [
    path('carts/', CartsView.as_view(), name='info'),
]