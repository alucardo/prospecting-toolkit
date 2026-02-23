from django.test import TestCase
from ...models import City, Lead, LeadKeyword


class LeadKeywordModelTest(TestCase):

    def setUp(self):
        self.city = City.objects.create(name="Warszawa")
        self.lead = Lead.objects.create(city=self.city, name="Jan Kowalski")

    def test_create_lead_keyword(self):
        """Tworzy słowo kluczowe powiązane z leadem"""
        keyword = LeadKeyword.objects.create(
            lead=self.lead,
            phrase="restauracja włoska warszawa"
        )

        self.assertEqual(keyword.lead, self.lead)
        self.assertEqual(keyword.phrase, "restauracja włoska warszawa")

    def test_lead_keyword_str(self):
        """Sprawdza czy __str__ zwraca frazę i nazwę leada"""
        keyword = LeadKeyword.objects.create(
            lead=self.lead,
            phrase="restauracja włoska warszawa"
        )

        self.assertEqual(str(keyword), "restauracja włoska warszawa (Jan Kowalski)")

    def test_lead_keyword_has_created_at(self):
        """Sprawdza czy created_at jest automatycznie ustawiane"""
        keyword = LeadKeyword.objects.create(
            lead=self.lead,
            phrase="restauracja włoska warszawa"
        )

        self.assertIsNotNone(keyword.created_at)

    def test_lead_can_have_multiple_keywords(self):
        """Lead może mieć wiele słów kluczowych"""
        LeadKeyword.objects.create(lead=self.lead, phrase="restauracja włoska warszawa")
        LeadKeyword.objects.create(lead=self.lead, phrase="pizza warszawa centrum")
        LeadKeyword.objects.create(lead=self.lead, phrase="włoskie jedzenie warszawa")

        self.assertEqual(LeadKeyword.objects.count(), 3)

    def test_lead_keyword_ordering_by_created_at(self):
        """Słowa kluczowe są posortowane od najstarszego (ordering = created_at)"""
        first = LeadKeyword.objects.create(lead=self.lead, phrase="pierwsza fraza")
        second = LeadKeyword.objects.create(lead=self.lead, phrase="druga fraza")

        keywords = list(LeadKeyword.objects.all())

        self.assertEqual(keywords[0], first)
        self.assertEqual(keywords[1], second)

    def test_lead_keyword_is_deleted_when_lead_is_deleted(self):
        """Usunięcie leada usuwa też jego słowa kluczowe (on_delete=CASCADE)"""
        LeadKeyword.objects.create(lead=self.lead, phrase="restauracja włoska warszawa")

        self.lead.delete()

        self.assertEqual(LeadKeyword.objects.count(), 0)
