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


def _test_smtp(s):
    """Próbuje połączyć się z serwerem SMTP. Zwraca 'ok', 'error' lub None."""
    if not s.smtp_host or not s.smtp_username or not s.smtp_password:
        return None
    import smtplib
    try:
        if s.smtp_use_tls:
            srv = smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=8)
            srv.starttls()
        else:
            srv = smtplib.SMTP_SSL(s.smtp_host, s.smtp_port, timeout=8)
        srv.login(s.smtp_username, s.smtp_password)
        srv.quit()
        return 'ok'
    except Exception:
        return 'error'


def _test_imap(s):
    """Próbuje połączyć się z serwerem IMAP. Zwraca 'ok', 'error' lub None."""
    if not s.imap_host or not s.imap_username or not s.imap_password:
        return None
    import imaplib
    try:
        if s.imap_use_ssl:
            m = imaplib.IMAP4_SSL(s.imap_host, s.imap_port)
        else:
            m = imaplib.IMAP4(s.imap_host, s.imap_port)
        m.login(s.imap_username, s.imap_password)
        m.logout()
        return 'ok'
    except Exception:
        return 'error'


@login_required
def settings(request):
    app_settings = AppSettings.get()

    if request.method == 'POST':
        app_settings.openai_api_key = request.POST.get('openai_api_key', '').strip()
        app_settings.google_maps_api_key = request.POST.get('google_maps_api_key', '').strip()
        app_settings.dataforseo_login = request.POST.get('dataforseo_login', '').strip()
        app_settings.dataforseo_password = request.POST.get('dataforseo_password', '').strip()
        # SMTP
        app_settings.smtp_host = request.POST.get('smtp_host', '').strip()
        app_settings.smtp_port = int(request.POST.get('smtp_port', 587) or 587)
        app_settings.smtp_username = request.POST.get('smtp_username', '').strip()
        app_settings.smtp_from_email = request.POST.get('smtp_from_email', '').strip()
        app_settings.smtp_use_tls = 'smtp_use_tls' in request.POST
        if request.POST.get('smtp_password'):
            app_settings.smtp_password = request.POST.get('smtp_password')
        # IMAP
        app_settings.imap_host = request.POST.get('imap_host', '').strip()
        app_settings.imap_port = int(request.POST.get('imap_port', 993) or 993)
        app_settings.imap_username = request.POST.get('imap_username', '').strip()
        app_settings.imap_use_ssl = 'imap_use_ssl' in request.POST
        if request.POST.get('imap_password'):
            app_settings.imap_password = request.POST.get('imap_password')
        app_settings.save()
        messages.success(request, 'Ustawienia zostały zapisane.')
        return redirect('leads:settings')

    balance = get_apify_balance()
    openai_balance = get_openai_balance(app_settings.openai_api_key)
    dataforseo_balance = get_dataforseo_balance(app_settings.dataforseo_login, app_settings.dataforseo_password)
    smtp_status = _test_smtp(app_settings)
    imap_status = _test_imap(app_settings)

    context = {
        'balance': balance,
        'openai_balance': openai_balance,
        'dataforseo_balance': dataforseo_balance,
        'app_settings': app_settings,
        'smtp_status': smtp_status,
        'imap_status': imap_status,
    }
    return render(request, 'leads/settings.html', context)
