from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from ...models import City, Lead, CallLog


class DashboardViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.url = reverse('leads:dashboard')

    def test_dashboard_requires_login(self):
        """Niezalogowany użytkownik jest przekierowywany na stronę logowania"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_dashboard_returns_200_for_logged_in_user(self):
        """Zalogowany użytkownik widzi dashboard"""
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

    def test_dashboard_uses_correct_template(self):
        """Dashboard używa właściwego szablonu"""
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(self.url)

        self.assertTemplateUsed(response, 'leads/dashboard.html')

    def test_dashboard_context_contains_call_stats(self):
        """Kontekst zawiera statystyki połączeń"""
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(self.url)

        self.assertIn('calls_today', response.context)
        self.assertIn('calls_week', response.context)
        self.assertIn('calls_month', response.context)

    def test_dashboard_context_contains_effective_stats(self):
        """Kontekst zawiera statystyki efektywnych połączeń"""
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(self.url)

        self.assertIn('effective_today', response.context)
        self.assertIn('effective_week', response.context)
        self.assertIn('effective_month', response.context)

    def test_dashboard_calls_today_count(self):
        """Sprawdza czy calls_today zlicza poprawnie połączenia z dziś"""
        self.client.login(username="testuser", password="testpass")

        city = City.objects.create(name="Warszawa")
        lead = Lead.objects.create(city=city, name="Jan Kowalski")
        CallLog.objects.create(lead=lead, user=self.user, status=CallLog.STATUS_TALKED)
        CallLog.objects.create(lead=lead, user=self.user, status=CallLog.STATUS_NO_ANSWER)

        response = self.client.get(self.url)

        self.assertEqual(response.context['calls_today'], 2)

    def test_dashboard_shows_only_current_user_calls(self):
        """Dashboard pokazuje tylko połączenia zalogowanego usera"""
        self.client.login(username="testuser", password="testpass")

        other_user = User.objects.create_user(username="other", password="testpass")
        city = City.objects.create(name="Warszawa")
        lead = Lead.objects.create(city=city, name="Jan Kowalski")
        CallLog.objects.create(lead=lead, user=self.user, status=CallLog.STATUS_TALKED)
        CallLog.objects.create(lead=lead, user=other_user, status=CallLog.STATUS_TALKED)

        response = self.client.get(self.url)

        self.assertEqual(response.context['calls_today'], 1)

    def test_dashboard_context_contains_reminders(self):
        """Kontekst zawiera listę przypomnień"""
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(self.url)

        self.assertIn('reminders', response.context)
