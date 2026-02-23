from django.test import TestCase
from ...models import City, Lead, KeywordSuggestionBatch, KeywordSuggestion


class KeywordSuggestionBatchModelTest(TestCase):

    def setUp(self):
        self.city = City.objects.create(name="Warszawa")
        self.lead = Lead.objects.create(city=self.city, name="Jan Kowalski")

    def test_create_batch(self):
        """Tworzy batch powiązany z leadem"""
        batch = KeywordSuggestionBatch.objects.create(lead=self.lead)

        self.assertEqual(batch.lead, self.lead)

    def test_batch_default_status_is_pending(self):
        """Domyślny status batcha to 'pending'"""
        batch = KeywordSuggestionBatch.objects.create(lead=self.lead)

        self.assertEqual(batch.status, KeywordSuggestionBatch.STATUS_PENDING)

    def test_batch_default_error_message_is_empty(self):
        """Domyślnie error_message jest pustym stringiem"""
        batch = KeywordSuggestionBatch.objects.create(lead=self.lead)

        self.assertEqual(batch.error_message, "")

    def test_batch_str(self):
        """Sprawdza czy __str__ zwraca nazwę leada i datę"""
        batch = KeywordSuggestionBatch.objects.create(lead=self.lead)

        self.assertIn("Jan Kowalski", str(batch))

    def test_batch_is_deleted_when_lead_is_deleted(self):
        """Usunięcie leada usuwa też jego batche (on_delete=CASCADE)"""
        KeywordSuggestionBatch.objects.create(lead=self.lead)

        self.lead.delete()

        self.assertEqual(KeywordSuggestionBatch.objects.count(), 0)

    def test_batch_ordering_newest_first(self):
        """Batche są posortowane od najnowszego (ordering = -created_at)"""
        first = KeywordSuggestionBatch.objects.create(lead=self.lead)
        second = KeywordSuggestionBatch.objects.create(lead=self.lead)

        batches = list(KeywordSuggestionBatch.objects.all())

        self.assertEqual(batches[0], second)
        self.assertEqual(batches[1], first)


class KeywordSuggestionModelTest(TestCase):

    def setUp(self):
        self.city = City.objects.create(name="Warszawa")
        self.lead = Lead.objects.create(city=self.city, name="Jan Kowalski")
        self.batch = KeywordSuggestionBatch.objects.create(lead=self.lead)

    def test_create_suggestion(self):
        """Tworzy sugestię słowa kluczowego powiązaną z batchem"""
        suggestion = KeywordSuggestion.objects.create(
            batch=self.batch,
            phrase="restauracja włoska warszawa",
            volume=1200,
            ai_rank=3,
            ai_reason="Wysoki wolumen, niska konkurencja"
        )

        self.assertEqual(suggestion.batch, self.batch)
        self.assertEqual(suggestion.phrase, "restauracja włoska warszawa")
        self.assertEqual(suggestion.volume, 1200)
        self.assertEqual(suggestion.ai_rank, 3)

    def test_suggestion_default_ai_rank_is_zero(self):
        """Domyślny ai_rank to 0"""
        suggestion = KeywordSuggestion.objects.create(
            batch=self.batch,
            phrase="restauracja włoska warszawa"
        )

        self.assertEqual(suggestion.ai_rank, 0)

    def test_suggestion_volume_can_be_null(self):
        """Pole volume może być NULL"""
        suggestion = KeywordSuggestion.objects.create(
            batch=self.batch,
            phrase="restauracja włoska warszawa"
        )

        self.assertIsNone(suggestion.volume)

    def test_suggestion_str(self):
        """Sprawdza czy __str__ zwraca frazę i wolumen"""
        suggestion = KeywordSuggestion.objects.create(
            batch=self.batch,
            phrase="restauracja włoska warszawa",
            volume=1200
        )

        self.assertEqual(str(suggestion), "restauracja włoska warszawa (1200/mies.)")

    def test_suggestion_str_without_volume(self):
        """Sprawdza __str__ gdy volume jest NULL"""
        suggestion = KeywordSuggestion.objects.create(
            batch=self.batch,
            phrase="restauracja włoska warszawa"
        )

        self.assertEqual(str(suggestion), "restauracja włoska warszawa (?/mies.)")

    def test_suggestion_is_deleted_when_batch_is_deleted(self):
        """Usunięcie batcha usuwa też jego sugestie (on_delete=CASCADE)"""
        KeywordSuggestion.objects.create(
            batch=self.batch,
            phrase="restauracja włoska warszawa"
        )

        self.batch.delete()

        self.assertEqual(KeywordSuggestion.objects.count(), 0)
