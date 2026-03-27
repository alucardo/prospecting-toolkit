from django.urls import path
from . import views
from .views.scripts import script_index, script_create, script_edit, script_delete, script_detail

app_name = 'leads'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('cities/', views.city_index, name='city_index'),
    path('cities/new/', views.city_create, name='city_create'),
    path('cities/<int:pk>/', views.city_detail, name='city_detail'),
    path('cities/<int:pk>/edit/', views.city_edit, name='city_edit'),
    path('cities/<int:pk>/delete/', views.city_delete, name='city_delete'),
    path('cities/geocode/', views.city_geocode, name='city_geocode'),
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
    path('leads/<int:pk>/status-history/<int:history_pk>/delete/', views.lead_status_history_delete, name='lead_status_history_delete'),
    path('leads/<int:pk>/contacts/new/', views.lead_contact_create, name='lead_contact_create'),
    path('leads/<int:pk>/contacts/<int:contact_pk>/edit/', views.lead_contact_edit, name='lead_contact_edit'),
    path('leads/<int:pk>/contacts/<int:contact_pk>/delete/', views.lead_contact_delete, name='lead_contact_delete'),
    path('leads/<int:pk>/notes/new/', views.lead_note_create, name='lead_note_create'),
    path('leads/<int:pk>/notes/<int:note_pk>/edit/', views.lead_note_edit, name='lead_note_edit'),
    path('leads/<int:pk>/notes/<int:note_pk>/delete/', views.lead_note_delete, name='lead_note_delete'),
    path('settings/', views.settings, name='settings'),
    path('leads/<int:pk>/google/fetch/', views.google_business_fetch, name='google_business_fetch'),
    path('leads/<int:pk>/google/analyze/', views.google_business_analyze, name='google_business_analyze'),
    path('leads/<int:pk>/keywords/add/', views.lead_keyword_add, name='lead_keyword_add'),
    path('leads/<int:lead_pk>/keywords/<int:keyword_pk>/delete/', views.lead_keyword_delete, name='lead_keyword_delete'),
    path('leads/<int:pk>/keywords/check/', views.lead_keyword_check_rankings, name='lead_keyword_check_rankings'),
    path('leads/<int:lead_pk>/keywords/<int:keyword_pk>/check/', views.lead_keyword_check_single, name='lead_keyword_check_single'),
    path('leads/<int:pk>/keywords/suggest/', views.keyword_suggestions, name='keyword_suggestions'),
    path('leads/import-from-maps/', views.lead_import_from_maps, name='lead_import_from_maps'),
    path('whisper/transcribe/', views.whisper_transcribe, name='whisper_transcribe'),
    path('leads/search/phone/', views.phone_search, name='phone_search'),
    path('leads/<int:pk>/analysis/<int:analysis_pk>/posts-status/', views.analysis_posts_status, name='analysis_posts_status'),
    path('leads/<int:pk>/reports/google-analysis/', views.reports.google_analysis_pdf, name='report_google_analysis'),
    path('leads/<int:pk>/reports/google-analysis/preview/', views.reports.google_analysis_preview, name='report_google_analysis_preview'),
    path('leads/<int:pk>/reports/google-analysis/status/', views.reports.pdf_status, name='pdf_status'),
    path('leads/<int:pk>/audit/edit/', views.reports.audit_edit, name='audit_edit'),
    path('profile/', views.user_contact.user_contact_edit, name='user_contact_edit'),

    # Klienci
    path('klienci/', views.client.client_index, name='client_index'),
    path('klienci/<int:pk>/', views.client.client_detail, name='client_detail'),
    path('klienci/<int:pk>/snapshot/', views.client.client_snapshot_trigger, name='client_snapshot_trigger'),
    path('klienci/<int:pk>/check-rankings/', views.client.client_check_rankings, name='client_check_rankings'),

    # Frazy kluczowe województw
    path('frazy/', views.voivodeship_keywords.voivodeship_keyword_index, name='voivodeship_keyword_index'),
    path('frazy/<int:pk>/', views.voivodeship_keywords.voivodeship_keyword_detail, name='voivodeship_keyword_detail'),

    # Pipelines
    path('pipelines/', views.pipeline.pipeline_index, name='pipeline_index'),
    path('pipelines/new/', views.pipeline.pipeline_create, name='pipeline_create'),
    path('pipelines/<int:pk>/', views.pipeline.pipeline_detail, name='pipeline_detail'),
    path('pipelines/<int:pk>/edit/', views.pipeline.pipeline_edit, name='pipeline_edit'),
    path('pipelines/<int:pipeline_pk>/steps/new/', views.pipeline.pipeline_step_create, name='pipeline_step_create'),
    path('pipelines/<int:pipeline_pk>/steps/<int:step_pk>/edit/', views.pipeline.pipeline_step_edit, name='pipeline_step_edit'),
    path('pipelines/<int:pipeline_pk>/steps/<int:step_pk>/delete/', views.pipeline.pipeline_step_delete, name='pipeline_step_delete'),
    path('pipelines/<int:pipeline_pk>/steps.json', views.pipeline.pipeline_steps_json, name='pipeline_steps_json'),
    path('leads/<int:lead_pk>/pipeline/add/', views.pipeline.lead_pipeline_add, name='lead_pipeline_add'),
    path('leads/<int:lead_pk>/pipeline/move/', views.pipeline.lead_pipeline_move, name='lead_pipeline_move'),
    path('leads/<int:lead_pk>/pipeline/edit/', views.pipeline.lead_pipeline_edit, name='lead_pipeline_edit'),

    # Google Business Profile
    path('gbp/locations/', views.gbp.gbp_locations, name='gbp_locations'),

    # Log działań klientów
    path('leads/<int:lead_pk>/activity/', views.activity_log.activity_log_index, name='activity_log_index'),
    path('leads/<int:lead_pk>/activity/<int:pk>/edit/', views.activity_log.activity_log_edit, name='activity_log_edit'),
    path('leads/<int:lead_pk>/activity/<int:pk>/delete/', views.activity_log.activity_log_delete, name='activity_log_delete'),

    # Katalogi NAP
    path('nap/', views.nap.nap_directory_index, name='nap_directory_index'),
    path('nap/nowy/', views.nap.nap_directory_create, name='nap_directory_create'),
    path('nap/<int:pk>/edytuj/', views.nap.nap_directory_edit, name='nap_directory_edit'),
    path('nap/<int:pk>/usun/', views.nap.nap_directory_delete, name='nap_directory_delete'),
    path('nap/tagi/', views.nap.nap_tag_index, name='nap_tag_index'),
    path('nap/tagi/nowy/', views.nap.nap_tag_create, name='nap_tag_create'),
    path('nap/tagi/<int:pk>/edytuj/', views.nap.nap_tag_edit, name='nap_tag_edit'),
    path('nap/tagi/<int:pk>/usun/', views.nap.nap_tag_delete, name='nap_tag_delete'),

    # Skrypty rozmów
    path('skrypty/', script_index, name='script_index'),
    path('skrypty/nowy/', script_create, name='script_create'),
    path('skrypty/<int:pk>/', script_detail, name='script_detail'),
    path('skrypty/<int:pk>/edytuj/', script_edit, name='script_edit'),
    path('skrypty/<int:pk>/usun/', script_delete, name='script_delete'),
]