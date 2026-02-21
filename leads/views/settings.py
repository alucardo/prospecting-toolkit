from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from leads.services.apify import get_apify_balance


@login_required
def settings(request):
    balance = get_apify_balance()
    context = {
        'balance': balance,
    }
    return render(request, 'leads/settings.html', context)