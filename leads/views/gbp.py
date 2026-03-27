from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from ..models import Lead, AppSettings
from ..services.gbp_service import get_access_token, list_locations


@login_required
def gbp_locations(request):
    app_settings = AppSettings.get()
    error = None
    locations = []
    clients = Lead.objects.filter(status='client').order_by('name')

    if not app_settings.google_refresh_token:
        error = 'Brak autoryzacji Google. Przejdź do Ustawień i kliknij "Autoryzuj z Google".'
    else:
        try:
            access_token = get_access_token(app_settings.google_refresh_token)
            locs = list_locations(access_token)
            for loc in locs:
                locations.append({
                    'name': loc.get('name'),
                    'title': loc.get('title', '—'),
                    'address': _format_address(loc.get('storefrontAddress', {})),
                    'website': loc.get('websiteUri', ''),
                })
        except Exception as e:
            import requests as req_lib
            if isinstance(e, req_lib.HTTPError) and e.response is not None:
                error = f'HTTP {e.response.status_code}\n\n{e.response.text}'
            else:
                import traceback
                error = f'{e}\n\n{traceback.format_exc()}'

    if request.method == 'POST':
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
