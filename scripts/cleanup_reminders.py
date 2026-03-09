"""
Skrypt czyszczący nieaktualne przypomnienia.

Uruchomienie:
    python manage.py shell < scripts/cleanup_reminders.py

Logika: reminder powinien być nieaktywny jeśli lead miał jakikolwiek
kontakt (call log) NOWSZY niż samo to przypomnienie.
"""

from leads.models import CallLog

# Znajdź wszystkie aktywne przypomnienia
active = CallLog.objects.filter(is_reminder_active=True).select_related('lead')

to_deactivate = []
for reminder in active:
    # Czy istnieje nowszy call log dla tego samego leada?
    has_newer_contact = (
        CallLog.objects
        .filter(lead=reminder.lead, called_at__gt=reminder.called_at)
        .exclude(pk=reminder.pk)
        .exists()
    )
    if has_newer_contact:
        to_deactivate.append(reminder)

print(f"Aktywnych przypomnień łącznie: {active.count()}")
print(f"Do dezaktywacji (jest nowszy kontakt): {len(to_deactivate)}")

if to_deactivate:
    print("\nLista:")
    for r in to_deactivate:
        print(f"  [{r.pk}] {r.lead.name} — reminder z {r.called_at.strftime('%d.%m.%Y')}, next_contact: {r.next_contact_date.strftime('%d.%m.%Y') if r.next_contact_date else '—'}")

    confirm = input("\nDezaktywować? [t/N]: ").strip().lower()
    if confirm == 't':
        ids = [r.pk for r in to_deactivate]
        updated = CallLog.objects.filter(pk__in=ids).update(is_reminder_active=False)
        print(f"✓ Dezaktywowano {updated} przypomnień.")
    else:
        print("Anulowano.")
else:
    print("Nic do czyszczenia.")
