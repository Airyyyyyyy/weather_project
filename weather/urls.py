from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('delete/<str:city_name>/', views.delete_city, name='delete_city'),
    path('weather-chat/', views.weather_chat, name='weather_chat'),
]
