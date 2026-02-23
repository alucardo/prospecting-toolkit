from django.test import TestCase
from ...models import City, Lead


class LeadModelTest(TestCase):

    def setUp(self):
        # Lead wymaga City (ForeignKey), więc tworzymy je raz dla wszystkich testów
        self.city = City.objects.create(name="Warszawa")

    def test_create_lead_with_required_fields_only(self):
        """Tworzy leada z samym city — reszta pól ma domyślne wartości"""
        lead = Lead.objects.create(city=self.city)

        self.assertEqual(lead.city, self.city)

    def test_lead_default_status_is_new(self):
        """Domyślny status leada to 'new'"""
        lead = Lead.objects.create(city=self.city)

        self.assertEqual(lead.status, Lead.STATUS_NEW)

    def test_lead_default_source_is_google_maps(self):
        """Domyślne źródło leada to 'google_maps'"""
        lead = Lead.objects.create(city=self.city)

        self.assertEqual(lead.source, Lead.SOURCE_GOOGLE_MAPS)

    def test_lead_default_boolean_fields(self):
        """cold_email_sent i email_scraped domyślnie są False"""
        lead = Lead.objects.create(city=self.city)

        self.assertFalse(lead.cold_email_sent)
        self.assertFalse(lead.email_scraped)

    def test_create_lead_with_all_fields(self):
        """Tworzy leada z wypełnionymi wszystkimi polami"""
        lead = Lead.objects.create(
            city=self.city,
            name="Jan Kowalski",
            phone="123456789",
            email="jan@example.com",
            website="https://example.com",
            source=Lead.SOURCE_FILE,
            status=Lead.STATUS_INTERESTED,
        )

        self.assertEqual(lead.name, "Jan Kowalski")
        self.assertEqual(lead.phone, "123456789")
        self.assertEqual(lead.email, "jan@example.com")
        self.assertEqual(lead.source, Lead.SOURCE_FILE)
        self.assertEqual(lead.status, Lead.STATUS_INTERESTED)

    def test_lead_str(self):
        """Sprawdza czy __str__ zwraca nazwę i miasto"""
        lead = Lead.objects.create(city=self.city, name="Jan Kowalski")

        self.assertEqual(str(lead), "Jan Kowalski (Warszawa)")

    def test_lead_is_saved_in_database(self):
        """Sprawdza czy lead trafia do bazy"""
        Lead.objects.create(city=self.city, name="Jan Kowalski")

        self.assertEqual(Lead.objects.count(), 1)
