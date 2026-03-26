from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.conf import settings
from ..models import AppSettings
from ..services.gbp_service import get_authorization_url, exchange_code_for_tokens


def _redirect_uri(request):
    return request.build_absolute_uri('/google/oauth/callback/')


@login_required
def oauth_start(request):
    """Przekieruj do Google — rozpocznij flow OAuth2."""
    url = get_authorization_url(_redirect_uri(request))
    return redirect(url)


@login_required
def oauth_callback(request):
    """Google wraca tutaj z ?code=... — wymieniamy na refresh_token."""
    error = request.GET.get('error')
    if error:
        return HttpResponse(f'Błąd autoryzacji Google: {error}', status=400)

    code = request.GET.get('code')
    if not code:
        return HttpResponse('Brak kodu autoryzacji.', status=400)

    try:
        tokens = exchange_code_for_tokens(code, _redirect_uri(request))
    except Exception as e:
        return HttpResponse(f'Błąd wymiany tokenu: {e}', status=400)

    refresh_token = tokens.get('refresh_token')
    if not refresh_token:
        return HttpResponse(
            'Google nie zwróciło refresh_token. Upewnij się że consent screen ma prompt=consent.',
            status=400
        )

    app_settings = AppSettings.get()
    app_settings.google_refresh_token = refresh_token
    app_settings.save(update_fields=['google_refresh_token'])

    return redirect('/settings/?google=connected')
