from django.urls import path

from carts.views import CartsView, CartsSelectAllView, CartsSimpleView

urlpatterns = [
    path('carts/', CartsView.as_view(), name='info'),
    path('/carts/selection/', CartsSelectAllView .as_view()),
    path('/carts/simple/', CartsSimpleView.as_view(), name='simpleinfo'),
]