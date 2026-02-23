from django.test import TestCase
from ...models import City, Lead, LeadKeyword, KeywordRankCheck


class KeywordRankCheckModelTest(TestCase):

    def setUp(self):
        self.city = City.objects.create(name="Warszawa")
        self.lead = Lead.objects.create(city=self.city, name="Jan Kowalski")
        self.keyword = LeadKeyword.objects.create(
            lead=self.lead,
            phrase="restauracja włoska warszawa"
        )

    def test_create_rank_check_with_position(self):
        """Tworzy sprawdzenie pozycji z wynikiem"""
        rank_check = KeywordRankCheck.objects.create(
            keyword=self.keyword,
            position=5
        )

        self.assertEqual(rank_check.keyword, self.keyword)
        self.assertEqual(rank_check.position, 5)

    def test_create_rank_check_without_position(self):
        """Pozycja może być NULL — oznacza brak w top 20"""
        rank_check = KeywordRankCheck.objects.create(
            keyword=self.keyword,
            position=None
        )

        self.assertIsNone(rank_check.position)

    def test_rank_check_has_checked_at(self):
        """Sprawdza czy checked_at jest automatycznie ustawiane"""
        rank_check = KeywordRankCheck.objects.create(
            keyword=self.keyword,
            position=5
        )

        self.assertIsNotNone(rank_check.checked_at)

    def test_rank_check_str_with_position(self):
        """Sprawdza __str__ gdy pozycja jest znana"""
        rank_check = KeywordRankCheck.objects.create(
            keyword=self.keyword,
            position=5
        )

        self.assertIn("restauracja włoska warszawa", str(rank_check))
        self.assertIn("5", str(rank_check))

    def test_rank_check_str_without_position(self):
        """Sprawdza __str__ gdy pozycja jest NULL"""
        rank_check = KeywordRankCheck.objects.create(
            keyword=self.keyword,
            position=None
        )

        self.assertIn("brak", str(rank_check))

    def test_rank_check_ordering_newest_first(self):
        """Sprawdzenia są posortowane od najnowszego (ordering = -checked_at)"""
        first = KeywordRankCheck.objects.create(keyword=self.keyword, position=10)
        second = KeywordRankCheck.objects.create(keyword=self.keyword, position=5)

        rank_checks = list(KeywordRankCheck.objects.all())

        self.assertEqual(rank_checks[0], second)
        self.assertEqual(rank_checks[1], first)

    def test_rank_check_is_deleted_when_keyword_is_deleted(self):
        """Usunięcie słowa kluczowego usuwa też jego sprawdzenia (on_delete=CASCADE)"""
        KeywordRankCheck.objects.create(keyword=self.keyword, position=5)

        self.keyword.delete()

        self.assertEqual(KeywordRankCheck.objects.count(), 0)
