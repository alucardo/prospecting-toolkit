from django.urls import reverse
from django.test import TestCase
from django.contrib.auth.models import User
from leads.models import City, Lead


class PhoneSearchViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.url = reverse('leads:phone_search')

    def test_phone_search_requires_login(self):
        """Niezalogowany użytkownik jest przekierowywany na stronę logowania"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_redirect_when_empty_query(self):
        """Brak parametru q przekierowuje na listę leadów"""
        self.client.login(username="testuser", password="testpass")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('leads:lead_index'))

    def test_error_info_when_not_digit(self):
        """Gdy q nie zawiera cyfr, widok zwraca błąd"""
        self.client.login(username="testuser", password="testpass")

        response = self.client.get(self.url, {'q': 'abc'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['error'], 'Podaj numer telefonu.')

    def test_redirect_if_one_lead(self):
        """Gdy znaleziono dokładnie jeden lead, przekierowuje na jego szczegóły"""
        self.client.login(username="testuser", password="testpass")
        city = City.objects.create(name="test")
        lead_correct = Lead.objects.create(city=city, name="test", phone="123")
        lead_wrong = Lead.objects.create(city=city, name="wrong", phone="131")

        response = self.client.get(self.url, {'q': '123'})

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('leads:lead_detail', kwargs={'pk': lead_correct.pk}))

    def test_show_if_many_leads(self):
        """Gdy znaleziono więcej niż jeden lead, renderuje listę wyników"""
        self.client.login(username="testuser", password="testpass")
        city = City.objects.create(name="test")
        lead_1 = Lead.objects.create(city=city, name="test", phone="123")
        lead_2 = Lead.objects.create(city=city, name="wrong", phone="12 3")

        response = self.client.get(self.url, {'q': '123'})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'leads/phone_search.html')
        self.assertEqual(len(response.context['leads']), 2)
