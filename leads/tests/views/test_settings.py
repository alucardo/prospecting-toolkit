from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch
from ...models import AppSettings


class SettingsViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.url = reverse('leads:settings')

    def test_settings_requires_login(self):
        """Niezalogowany użytkownik jest przekierowywany na stronę logowania"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_settings_returns_200_for_logged_in_user(self):
        """Zalogowany użytkownik widzi stronę ustawień"""
        self.client.login(username="testuser", password="testpass")

        with patch('leads.views.settings.get_apify_balance', return_value=None), \
             patch('leads.views.settings.get_openai_balance', return_value=None), \
             patch('leads.views.settings.get_dataforseo_balance', return_value=None):

            response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

    def test_settings_uses_correct_template(self):
        """Widok używa właściwego szablonu"""
        self.client.login(username="testuser", password="testpass")

        with patch('leads.views.settings.get_apify_balance', return_value=None), \
             patch('leads.views.settings.get_openai_balance', return_value=None), \
             patch('leads.views.settings.get_dataforseo_balance', return_value=None):

            response = self.client.get(self.url)

        self.assertTemplateUsed(response, 'leads/settings.html')

    def test_settings_context_contains_app_settings(self):
        """Kontekst zawiera obiekt app_settings"""
        self.client.login(username="testuser", password="testpass")

        with patch('leads.views.settings.get_apify_balance', return_value=None), \
             patch('leads.views.settings.get_openai_balance', return_value=None), \
             patch('leads.views.settings.get_dataforseo_balance', return_value=None):

            response = self.client.get(self.url)

        self.assertIn('app_settings', response.context)

    def test_post_saves_settings(self):
        """POST zapisuje ustawienia i przekierowuje"""
        self.client.login(username="testuser", password="testpass")

        response = self.client.post(self.url, {
            'openai_api_key': 'sk-test-1234',
            'dataforseo_login': 'login@example.com',
            'dataforseo_password': 'tajnehaslo',
        })

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url)

        app_settings = AppSettings.get()
        self.assertEqual(app_settings.openai_api_key, 'sk-test-1234')
        self.assertEqual(app_settings.dataforseo_login, 'login@example.com')
        self.assertEqual(app_settings.dataforseo_password, 'tajnehaslo')

    def test_context_shows_openai_balance_when_active(self):
        """Kontekst zawiera status OpenAI gdy klucz jest aktywny"""
        self.client.login(username="testuser", password="testpass")

        with patch('leads.views.settings.get_apify_balance', return_value=None), \
             patch('leads.views.settings.get_openai_balance', return_value={'active': True}), \
             patch('leads.views.settings.get_dataforseo_balance', return_value=None):

            response = self.client.get(self.url)

        self.assertEqual(response.context['openai_balance'], {'active': True})

    def test_context_shows_dataforseo_balance(self):
        """Kontekst zawiera saldo DataForSEO"""
        self.client.login(username="testuser", password="testpass")

        with patch('leads.views.settings.get_apify_balance', return_value=None), \
             patch('leads.views.settings.get_openai_balance', return_value=None), \
             patch('leads.views.settings.get_dataforseo_balance', return_value={'balance': 9.99, 'spent': 0.01}):

            response = self.client.get(self.url)

        self.assertEqual(response.context['dataforseo_balance'], {'balance': 9.99, 'spent': 0.01})
