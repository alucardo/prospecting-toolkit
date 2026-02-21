from django.urls import path
from . import views

app_name = 'leads'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('settings/', views.settings, name='settings'),
    path('cities/', views.city_index, name='city_index'),
    path('cities/new/', views.city_create, name='city_create'),
    path('cities/<int:pk>/', views.city_detail, name='city_detail'),
    path('cities/<int:pk>/edit/', views.city_edit, name='city_edit'),
    path('cities/<int:pk>/delete/', views.city_delete, name='city_delete'),
]