from django.test import TestCase
from ...models import AppSettings


class AppSettingsModelTest(TestCase):

    def test_get_creates_instance_if_not_exists(self):
        """Metoda get() tworzy rekord jeśli nie istnieje"""
        settings = AppSettings.get()

        self.assertIsNotNone(settings)
        self.assertEqual(AppSettings.objects.count(), 1)

    def test_get_returns_same_instance(self):
        """Metoda get() zawsze zwraca ten sam rekord (singleton)"""
        first = AppSettings.get()
        second = AppSettings.get()

        self.assertEqual(first.pk, second.pk)
        self.assertEqual(AppSettings.objects.count(), 1)

    def test_default_fields_are_empty(self):
        """Domyślnie wszystkie pola są pustymi stringami"""
        settings = AppSettings.get()

        self.assertEqual(settings.openai_api_key, "")
        self.assertEqual(settings.dataforseo_login, "")
        self.assertEqual(settings.dataforseo_password, "")

    def test_save_and_retrieve_openai_api_key(self):
        """Sprawdza czy klucz API OpenAI zapisuje się poprawnie"""
        settings = AppSettings.get()
        settings.openai_api_key = "sk-test-1234"
        settings.save()

        retrieved = AppSettings.get()
        self.assertEqual(retrieved.openai_api_key, "sk-test-1234")

    def test_save_and_retrieve_dataforseo_credentials(self):
        """Sprawdza czy dane logowania DataForSEO zapisują się poprawnie"""
        settings = AppSettings.get()
        settings.dataforseo_login = "login@example.com"
        settings.dataforseo_password = "tajnehaslo"
        settings.save()

        retrieved = AppSettings.get()
        self.assertEqual(retrieved.dataforseo_login, "login@example.com")
        self.assertEqual(retrieved.dataforseo_password, "tajnehaslo")

    def test_app_settings_str(self):
        """Sprawdza czy __str__ zwraca właściwą nazwę"""
        settings = AppSettings.get()

        self.assertEqual(str(settings), "Ustawienia aplikacji")
