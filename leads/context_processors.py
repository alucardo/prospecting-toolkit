def app_settings_context(request):
    """Przekazuje globalne ustawienia aplikacji do każdego szablonu."""
    if not request.user.is_authenticated:
        return {}
    try:
        from leads.models import AppSettings
        settings = AppSettings.get()
        return {
            'global_has_unread_emails': settings.has_unread_emails,
            'global_unread_checked_at': settings.unread_emails_checked_at,
        }
    except Exception:
        return {}
