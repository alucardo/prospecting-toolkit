from django.urls import path
from . import views

app_name = 'leads'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('cities/', views.city_index, name='city_index'),
    path('cities/new/', views.city_create, name='city_create'),
    path('cities/<int:pk>/', views.city_detail, name='city_detail'),
    path('cities/<int:pk>/edit/', views.city_edit, name='city_edit'),
    path('cities/<int:pk>/delete/', views.city_delete, name='city_delete'),
    path('imports/new/', views.import_upload, name='import_upload'),
    path('imports/<int:pk>/map/', views.import_map, name='import_map'),
    path('leads/', views.lead_index, name='lead_index'),
    path('leads/new/', views.lead_create, name='lead_create'),
    path('leads/<int:pk>/', views.lead_detail, name='lead_detail'),
    path('leads/<int:pk>/edit/', views.lead_edit, name='lead_edit'),
    path('leads/<int:pk>/delete/', views.lead_delete, name='lead_delete'),
    path('leads/bulk-action/', views.lead_bulk_action, name='lead_bulk_action'),
    path('leads/<int:pk>/calls/new/', views.call_log_create, name='call_log_create'),
    path('leads/<int:pk>/calls/<int:call_pk>/edit/', views.call_log_edit, name='call_log_edit'),
    path('leads/<int:pk>/calls/<int:call_pk>/delete/', views.call_log_delete, name='call_log_delete'),
    path('leads/<int:pk>/scrape-email/', views.lead_scrape_email, name='lead_scrape_email'),
    path('leads/<int:pk>/notes/new/', views.lead_note_create, name='lead_note_create'),
    path('leads/<int:pk>/notes/<int:note_pk>/edit/', views.lead_note_edit, name='lead_note_edit'),
    path('leads/<int:pk>/notes/<int:note_pk>/delete/', views.lead_note_delete, name='lead_note_delete'),
    path('settings/', views.settings, name='settings'),
]