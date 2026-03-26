from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ..models import Lead, AppSettings
from ..services.gbp_service import get_access_token, list_accounts, list_locations


@login_required
def gbp_locations(request):
    """Widok do przypisywania lokalizacji GBP do klientów."""
    app_settings = AppSettings.get()
    error = None
    locations = []
    clients = Lead.objects.filter(status='client').order_by('name')

    if not app_settings.google_refresh_token:
        error = 'Brak autoryzacji Google. Przejdź do Ustawień i kliknij "Autoryzuj z Google".'
    else:
        try:
            access_token = get_access_token(app_settings.google_refresh_token)
            accounts = list_accounts(access_token)
            for account in accounts:
                account_name = account.get('name')
                locs = list_locations(access_token, account_name)
                for loc in locs:
                    locations.append({
                        'name': loc.get('name'),          # locations/123456789
                        'title': loc.get('title', '—'),
                        'address': _format_address(loc.get('storefrontAddress', {})),
                        'website': loc.get('websiteUri', ''),
                    })
        except Exception as e:
            error = f'Błąd pobierania lokalizacji: {e}'

    if request.method == 'POST':
        # Zapisz przypisania: POST zawiera lead_<pk> = location_name
        for key, value in request.POST.items():
            if key.startswith('lead_'):
                try:
                    lead_pk = int(key[5:])
                    lead = Lead.objects.get(pk=lead_pk, status='client')
                    lead.gbp_location_name = value.strip()
                    lead.save(update_fields=['gbp_location_name'])
                except (Lead.DoesNotExist, ValueError):
                    pass
        return redirect('leads:gbp_locations')

    return render(request, 'leads/gbp/locations.html', {
        'clients': clients,
        'locations': locations,
        'error': error,
    })


def _format_address(addr):
    if not addr:
        return ''
    parts = addr.get('addressLines', [])
    city = addr.get('locality', '')
    return ', '.join(filter(None, parts + [city]))
