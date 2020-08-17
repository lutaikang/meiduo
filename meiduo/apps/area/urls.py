from django.urls import path

from area import views

urlpatterns = [
    path('areas/', views.AreasView.as_view()),
]
