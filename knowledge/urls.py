from django.urls import path
from .views import tags, videos

app_name = 'knowledge'

urlpatterns = [
    # Ustawienia
    path('baza-wiedzy/ustawienia/', videos.knowledge_settings, name='settings'),

    # Tagi
    path('baza-wiedzy/tagi/', tags.tag_index, name='tag_index'),

    # Wideo inspiracje
    path('baza-wiedzy/wideo/', videos.video_index, name='video_index'),
    path('baza-wiedzy/wideo/nowa/', videos.video_create, name='video_create'),
    path('baza-wiedzy/wideo/<int:pk>/edytuj/', videos.video_edit, name='video_edit'),
    path('baza-wiedzy/wideo/<int:pk>/usun/', videos.video_delete, name='video_delete'),
]
