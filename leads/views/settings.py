from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from leads.services.apify import get_apify_balance
from leads.models import AppSettings


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
    context = {
        'balance': balance,
        'app_settings': app_settings,
    }
    return render(request, 'leads/settings.html', context)
