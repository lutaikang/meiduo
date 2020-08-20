from django.urls import path

from areas import views

urlpatterns = [
    path('areas/', views.AreasView.as_view()),
]
