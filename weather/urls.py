from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('delete/<str:city_name>/', views.delete_city, name='delete_city'),
]
