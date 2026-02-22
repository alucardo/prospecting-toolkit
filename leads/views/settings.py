from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from leads.services.apify import get_apify_balance
from leads.models import AppSettings
import requests
import base64


def get_openai_balance(api_key):
    if not api_key:
        return None
    try:
        resp = requests.get(
            'https://api.openai.com/v1/models',
            headers={'Authorization': f'Bearer {api_key}'},
            timeout=10,
        )
        if resp.status_code == 200:
            return {'active': True}
        return {'error': True}
    except Exception:
        return None


def get_dataforseo_balance(login, password):
    if not login or not password:
        return None
    try:
        credentials = base64.b64encode(f'{login}:{password}'.encode()).decode()
        resp = requests.get(
            'https://api.dataforseo.com/v3/appendix/user_data',
            headers={'Authorization': f'Basic {credentials}'},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            info = data.get('tasks', [{}])[0].get('result', [{}])[0] or {}
            money = info.get('money', {})
            return {
                'balance': round(money.get('balance', 0), 2),
                'spent': round(money.get('spent_today', 0), 4),
            }
    except Exception:
        pass
    return None


@login_required
def settings(request):
    app_settings = AppSettings.get()

    if request.method == 'POST':
        app_settings.openai_api_key = request.POST.get('openai_api_key', '').strip()
        app_settings.dataforseo_login = request.POST.get('dataforseo_login', '').strip()
        app_settings.dataforseo_password = request.POST.get('dataforseo_password', '').strip()
        app_settings.save()
        messages.success(request, 'Ustawienia zostały zapisane.')
        return redirect('leads:settings')

    balance = get_apify_balance()
    openai_balance = get_openai_balance(app_settings.openai_api_key)
    dataforseo_balance = get_dataforseo_balance(app_settings.dataforseo_login, app_settings.dataforseo_password)

    context = {
        'balance': balance,
        'openai_balance': openai_balance,
        'dataforseo_balance': dataforseo_balance,
        'app_settings': app_settings,
    }
    return render(request, 'leads/settings.html', context)
