from django.test import TestCase
from django.contrib.auth.models import User
from ...models import City, Lead, LeadStatusHistory


class LeadStatusHistoryModelTest(TestCase):

    def setUp(self):
        self.city = City.objects.create(name="Warszawa")
        self.lead = Lead.objects.create(city=self.city, name="Jan Kowalski")
        self.user = User.objects.create_user(username="testuser", password="testpass")

    def test_create_lead_status_history(self):
        """Tworzy wpis historii statusu powiązany z leadem i userem"""
        history = LeadStatusHistory.objects.create(
            lead=self.lead,
            user=self.user,
            status=Lead.STATUS_INTERESTED
        )

        self.assertEqual(history.lead, self.lead)
        self.assertEqual(history.user, self.user)
        self.assertEqual(history.status, Lead.STATUS_INTERESTED)

    def test_create_lead_status_history_without_user(self):
        """Historia statusu może istnieć bez usera (null=True)"""
        history = LeadStatusHistory.objects.create(
            lead=self.lead,
            user=None,
            status=Lead.STATUS_NEW
        )

        self.assertIsNone(history.user)

    def test_lead_status_history_has_changed_at(self):
        """Sprawdza czy changed_at jest automatycznie ustawiane"""
        history = LeadStatusHistory.objects.create(
            lead=self.lead,
            status=Lead.STATUS_NEW
        )

        self.assertIsNotNone(history.changed_at)

    def test_lead_status_history_get_status_display(self):
        """Sprawdza czy get_status_display zwraca polską nazwę statusu"""
        history = LeadStatusHistory.objects.create(
            lead=self.lead,
            status=Lead.STATUS_INTERESTED
        )

        self.assertEqual(history.get_status_display(), "Zainteresowany")

    def test_lead_can_have_multiple_status_history_entries(self):
        """Lead może mieć wiele wpisów historii statusu"""
        LeadStatusHistory.objects.create(lead=self.lead, status=Lead.STATUS_NEW)
        LeadStatusHistory.objects.create(lead=self.lead, status=Lead.STATUS_TALKED)
        LeadStatusHistory.objects.create(lead=self.lead, status=Lead.STATUS_INTERESTED)

        self.assertEqual(LeadStatusHistory.objects.count(), 3)

    def test_lead_status_history_is_deleted_when_lead_is_deleted(self):
        """Usunięcie leada usuwa też jego historię statusów (on_delete=CASCADE)"""
        LeadStatusHistory.objects.create(lead=self.lead, status=Lead.STATUS_NEW)

        self.lead.delete()

        self.assertEqual(LeadStatusHistory.objects.count(), 0)
