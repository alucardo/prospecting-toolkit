from django.test import TestCase
from ...models import City, Lead, LeadContact


class LeadContactModelTest(TestCase):

    def setUp(self):
        self.city = City.objects.create(name="Warszawa")
        self.lead = Lead.objects.create(city=self.city, name="Jan Kowalski")

    def test_create_lead_contact_with_required_fields(self):
        """Tworzy kontakt z wymaganym polem name"""
        contact = LeadContact.objects.create(
            lead=self.lead,
            name="Anna Nowak"
        )

        self.assertEqual(contact.lead, self.lead)
        self.assertEqual(contact.name, "Anna Nowak")

    def test_create_lead_contact_with_all_fields(self):
        """Tworzy kontakt z wypełnionymi wszystkimi polami"""
        contact = LeadContact.objects.create(
            lead=self.lead,
            name="Anna Nowak",
            phone="123456789",
            email="anna@example.com",
            note="Właścicielka"
        )

        self.assertEqual(contact.name, "Anna Nowak")
        self.assertEqual(contact.phone, "123456789")
        self.assertEqual(contact.email, "anna@example.com")
        self.assertEqual(contact.note, "Właścicielka")

    def test_lead_contact_default_optional_fields_are_empty(self):
        """Pola phone, email i note domyślnie są pustymi stringami"""
        contact = LeadContact.objects.create(
            lead=self.lead,
            name="Anna Nowak"
        )

        self.assertEqual(contact.phone, "")
        self.assertEqual(contact.email, "")
        self.assertEqual(contact.note, "")

    def test_lead_contact_str(self):
        """Sprawdza czy __str__ zwraca imię kontaktu i nazwę leada"""
        contact = LeadContact.objects.create(
            lead=self.lead,
            name="Anna Nowak"
        )

        self.assertEqual(str(contact), "Anna Nowak (Jan Kowalski)")

    def test_lead_contact_is_deleted_when_lead_is_deleted(self):
        """Usunięcie leada usuwa też jego kontakty (on_delete=CASCADE)"""
        LeadContact.objects.create(
            lead=self.lead,
            name="Anna Nowak"
        )

        self.lead.delete()

        self.assertEqual(LeadContact.objects.count(), 0)

    def test_lead_can_have_multiple_contacts(self):
        """Lead może mieć wiele kontaktów"""
        LeadContact.objects.create(lead=self.lead, name="Anna Nowak")
        LeadContact.objects.create(lead=self.lead, name="Piotr Wiśniewski")

        self.assertEqual(LeadContact.objects.count(), 2)
