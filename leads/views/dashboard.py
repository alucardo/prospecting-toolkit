from django.shortcuts import render
from leads.services.apify import get_apify_balance


def dashboard(request):
    balance = get_apify_balance()
    context = {
        'balance': balance,
    }
    return render(request, 'leads/dashboard.html', context)