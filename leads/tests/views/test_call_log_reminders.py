from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from ...models import City, Lead, CallLog


class ReminderLogicTest(TestCase):
    """Testy logiki przypomnień przy tworzeniu call loga."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client.login(username="testuser", password="testpass")
        city = City.objects.create(name="Warszawa")
        self.lead = Lead.objects.create(city=city, name="Testowa Firma")
        self.url = reverse('leads:call_log_create', kwargs={'pk': self.lead.pk})

    def _post_call_log(self, status='talked', next_contact_date=''):
        return self.client.post(self.url, {
            'type': 'call',
            'status': status,
            'note': '',
            'next_contact_date': next_contact_date,
        })

    # --- is_reminder_active przy tworzeniu ---

    def test_new_call_log_with_next_contact_sets_reminder_active(self):
        """Nowy call log z datą następnego kontaktu → is_reminder_active=True"""
        future = (timezone.now() + timezone.timedelta(days=7)).strftime('%Y-%m-%dT%H:%M')
        self._post_call_log(next_contact_date=future)

        log = CallLog.objects.get(lead=self.lead)
        self.assertTrue(log.is_reminder_active)

    def test_new_call_log_without_next_contact_no_reminder(self):
        """Nowy call log bez daty następnego kontaktu → is_reminder_active=False"""
        self._post_call_log(status='talked')

        log = CallLog.objects.get(lead=self.lead)
        self.assertFalse(log.is_reminder_active)

    # --- Dezaktywacja starych przypomnień ---

    def test_new_call_log_deactivates_old_reminders(self):
        """Dodanie nowego call loga dezaktywuje stare przypomnienia tego leada."""
        future = timezone.now() + timezone.timedelta(days=7)
        old = CallLog.objects.create(
            lead=self.lead,
            user=self.user,
            status='call_later',
            next_contact_date=future,
            is_reminder_active=True,
        )

        self._post_call_log(status='talked')  # nowy log bez next_contact_date

        old.refresh_from_db()
        self.assertFalse(old.is_reminder_active)

    def test_new_call_log_with_next_contact_deactivates_old_and_activates_new(self):
        """Nowy log z datą: stare przypomnienie gaśnie, nowe się zapala."""
        future = timezone.now() + timezone.timedelta(days=7)
        old = CallLog.objects.create(
            lead=self.lead,
            user=self.user,
            status='call_later',
            next_contact_date=future,
            is_reminder_active=True,
        )

        new_future = (timezone.now() + timezone.timedelta(days=14)).strftime('%Y-%m-%dT%H:%M')
        self._post_call_log(next_contact_date=new_future)

        old.refresh_from_db()
        new = CallLog.objects.order_by('-called_at').first()

        self.assertFalse(old.is_reminder_active)
        self.assertTrue(new.is_reminder_active)

    def test_multiple_old_reminders_all_deactivated(self):
        """Kilka starych przypomnień — wszystkie gasną po nowym logu."""
        future = timezone.now() + timezone.timedelta(days=7)
        logs = [
            CallLog.objects.create(
                lead=self.lead,
                user=self.user,
                status='call_later',
                next_contact_date=future,
                is_reminder_active=True,
            )
            for _ in range(3)
        ]

        self._post_call_log(status='talked')

        for log in logs:
            log.refresh_from_db()
            self.assertFalse(log.is_reminder_active)

    def test_reminder_of_other_lead_not_affected(self):
        """Przypomnienie innego leada nie jest dezaktywowane."""
        other_lead = Lead.objects.create(
            city=City.objects.get(name="Warszawa"),
            name="Inna Firma",
        )
        future = timezone.now() + timezone.timedelta(days=7)
        other_reminder = CallLog.objects.create(
            lead=other_lead,
            user=self.user,
            status='call_later',
            next_contact_date=future,
            is_reminder_active=True,
        )

        self._post_call_log(status='talked')

        other_reminder.refresh_from_db()
        self.assertTrue(other_reminder.is_reminder_active)


class DashboardReminderTest(TestCase):
    """Testy wyświetlania przypomnień na dashboardzie."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client.login(username="testuser", password="testpass")
        city = City.objects.create(name="Kraków")
        self.lead = Lead.objects.create(city=city, name="Testowa Firma")
        self.url = reverse('leads:dashboard')

    def _make_reminder(self, days_offset, user=None):
        """Tworzy call log z aktywnym przypomnieniem za N dni (ujemny = w przeszłości)."""
        return CallLog.objects.create(
            lead=self.lead,
            user=user or self.user,
            status='call_later',
            next_contact_date=timezone.now() + timezone.timedelta(days=days_offset),
            is_reminder_active=True,
        )

    def test_past_reminder_shown_on_dashboard(self):
        """Przeterminowane przypomnienie pojawia się na dashboardzie."""
        self._make_reminder(days_offset=-1)
        response = self.client.get(self.url)
        self.assertEqual(len(response.context['reminders']), 1)

    def test_todays_reminder_shown_on_dashboard(self):
        """Przypomnienie na dziś pojawia się na dashboardzie."""
        self._make_reminder(days_offset=0)
        response = self.client.get(self.url)
        self.assertEqual(len(response.context['reminders']), 1)

    def test_tomorrows_reminder_shown_on_dashboard(self):
        """Przypomnienie na jutro pojawia się na dashboardzie."""
        self._make_reminder(days_offset=1)
        response = self.client.get(self.url)
        self.assertEqual(len(response.context['reminders']), 1)

    def test_future_reminder_not_shown_on_dashboard(self):
        """Przypomnienie za 2+ dni NIE pojawia się na dashboardzie."""
        self._make_reminder(days_offset=2)
        response = self.client.get(self.url)
        self.assertEqual(len(response.context['reminders']), 0)

    def test_inactive_reminder_not_shown(self):
        """Nieaktywne przypomnienie (is_reminder_active=False) nie pojawia się."""
        CallLog.objects.create(
            lead=self.lead,
            user=self.user,
            status='call_later',
            next_contact_date=timezone.now() - timezone.timedelta(days=1),
            is_reminder_active=False,
        )
        response = self.client.get(self.url)
        self.assertEqual(len(response.context['reminders']), 0)

    def test_other_users_reminder_not_shown(self):
        """Przypomnienie innego użytkownika nie pojawia się na moim dashboardzie."""
        other = User.objects.create_user(username="other", password="pass")
        self._make_reminder(days_offset=-1, user=other)
        response = self.client.get(self.url)
        self.assertEqual(len(response.context['reminders']), 0)

    def test_after_new_call_log_reminder_disappears_from_dashboard(self):
        """
        Scenariusz end-to-end:
        1. Jest aktywne przypomnienie
        2. Dodajemy nowy call log (bez next_contact_date)
        3. Przypomnienie znika z dashboardu
        """
        self._make_reminder(days_offset=-1)

        # Weryfikacja — przed nowym logiem przypomnienie jest widoczne
        response = self.client.get(self.url)
        self.assertEqual(len(response.context['reminders']), 1)

        # Nowy call log bez daty następnego kontaktu
        self.client.post(
            reverse('leads:call_log_create', kwargs={'pk': self.lead.pk}),
            {'type': 'call', 'status': 'talked', 'note': '', 'next_contact_date': ''},
        )

        # Przypomnienie powinno zniknąć
        response = self.client.get(self.url)
        self.assertEqual(len(response.context['reminders']), 0)
