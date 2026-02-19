from django.urls import path
from . import views

app_name = 'leads'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('cities/', views.city_index, name='city_index'),
    path('cities/new/', views.city_create, name='city_create'),
    path('cities/<int:pk>/', views.city_detail, name='city_detail'),
]