from django.test import TestCase
from ...models import City, SearchQuery


class SearchQueryModelTest(TestCase):

    def setUp(self):
        self.city = City.objects.create(name="Warszawa")

    def test_create_search_query(self):
        """Tworzy zapytanie z wymaganymi polami"""
        search_query = SearchQuery.objects.create(
            city=self.city,
            keyword="restauracja"
        )

        self.assertEqual(search_query.city, self.city)
        self.assertEqual(search_query.keyword, "restauracja")

    def test_default_source_is_google_maps(self):
        """Domyślne źródło to 'google_maps'"""
        search_query = SearchQuery.objects.create(
            city=self.city,
            keyword="restauracja"
        )

        self.assertEqual(search_query.source, SearchQuery.SOURCE_GOOGLE_MAPS)

    def test_default_limit_is_100(self):
        """Domyślny limit wyników to 100"""
        search_query = SearchQuery.objects.create(
            city=self.city,
            keyword="restauracja"
        )

        self.assertEqual(search_query.limit, 100)

    def test_default_status_is_pending(self):
        """Domyślny status to 'pending'"""
        search_query = SearchQuery.objects.create(
            city=self.city,
            keyword="restauracja"
        )

        self.assertEqual(search_query.status, "pending")

    def test_default_apify_run_id_is_empty(self):
        """Domyślnie apify_run_id jest pustym stringiem"""
        search_query = SearchQuery.objects.create(
            city=self.city,
            keyword="restauracja"
        )

        self.assertEqual(search_query.apify_run_id, "")

    def test_search_query_str(self):
        """Sprawdza czy __str__ zwraca keyword, miasto i status"""
        search_query = SearchQuery.objects.create(
            city=self.city,
            keyword="restauracja"
        )

        self.assertEqual(str(search_query), "restauracja - Warszawa (pending)")

    def test_search_query_is_deleted_when_city_is_deleted(self):
        """Usunięcie miasta usuwa też jego zapytania (on_delete=CASCADE)"""
        SearchQuery.objects.create(
            city=self.city,
            keyword="restauracja"
        )

        self.city.delete()

        self.assertEqual(SearchQuery.objects.count(), 0)
