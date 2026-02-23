from django.test import TestCase
from ...models import City, Lead, LeadNote


class LeadNoteModelTest(TestCase):

    def setUp(self):
        self.city = City.objects.create(name="Warszawa")
        self.lead = Lead.objects.create(city=self.city, name="Jan Kowalski")

    def test_create_lead_note(self):
        """Tworzy notatkę powiązaną z leadem"""
        note = LeadNote.objects.create(
            lead=self.lead,
            content="Zadzwonić po 15:00"
        )

        self.assertEqual(note.lead, self.lead)
        self.assertEqual(note.content, "Zadzwonić po 15:00")

    def test_lead_note_str(self):
        """Sprawdza czy __str__ zwraca nazwę leada i datę"""
        note = LeadNote.objects.create(
            lead=self.lead,
            content="Zadzwonić po 15:00"
        )

        self.assertIn("Jan Kowalski", str(note))

    def test_lead_note_has_created_at(self):
        """Sprawdza czy created_at jest automatycznie ustawiane"""
        note = LeadNote.objects.create(
            lead=self.lead,
            content="Zadzwonić po 15:00"
        )

        self.assertIsNotNone(note.created_at)

    def test_lead_note_has_updated_at(self):
        """Sprawdza czy updated_at zmienia się po edycji"""
        note = LeadNote.objects.create(
            lead=self.lead,
            content="Zadzwonić po 15:00"
        )
        created_at = note.updated_at

        note.content = "Zmieniona treść"
        note.save()

        self.assertGreaterEqual(note.updated_at, created_at)

    def test_lead_note_is_deleted_when_lead_is_deleted(self):
        """Usunięcie leada usuwa też jego notatki (on_delete=CASCADE)"""
        LeadNote.objects.create(
            lead=self.lead,
            content="Zadzwonić po 15:00"
        )

        self.lead.delete()

        self.assertEqual(LeadNote.objects.count(), 0)

    def test_lead_note_is_saved_in_database(self):
        """Sprawdza czy notatka trafia do bazy"""
        LeadNote.objects.create(
            lead=self.lead,
            content="Zadzwonić po 15:00"
        )

        self.assertEqual(LeadNote.objects.count(), 1)
