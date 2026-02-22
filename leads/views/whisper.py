from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from leads.models import AppSettings
import requests


@login_required
@require_POST
def whisper_transcribe(request):
    audio_file = request.FILES.get('audio')
    if not audio_file:
        return JsonResponse({'error': 'Brak pliku audio'}, status=400)

    app_settings = AppSettings.get()
    if not app_settings.openai_api_key:
        return JsonResponse({'error': 'Brak klucza OpenAI API w ustawieniach'}, status=400)

    try:
        response = requests.post(
            'https://api.openai.com/v1/audio/transcriptions',
            headers={'Authorization': f'Bearer {app_settings.openai_api_key}'},
            files={'file': (audio_file.name or 'recording.webm', audio_file, audio_file.content_type or 'audio/webm')},
            data={'model': 'whisper-1', 'language': 'pl'},
            timeout=30,
        )
        response.raise_for_status()
        text = response.json().get('text', '')
        return JsonResponse({'text': text})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
