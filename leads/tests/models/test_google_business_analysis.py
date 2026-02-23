from django.test import TestCase
from ...models import City, Lead, GoogleBusinessAnalysis


class GoogleBusinessAnalysisModelTest(TestCase):

    def setUp(self):
        self.city = City.objects.create(name="Warszawa")
        self.lead = Lead.objects.create(city=self.city, name="Jan Kowalski")

    def test_create_analysis(self):
        """Tworzy analizę powiązaną z leadem"""
        analysis = GoogleBusinessAnalysis.objects.create(lead=self.lead)

        self.assertEqual(analysis.lead, self.lead)

    def test_default_status_is_fetched(self):
        """Domyślny status analizy to 'fetched'"""
        analysis = GoogleBusinessAnalysis.objects.create(lead=self.lead)

        self.assertEqual(analysis.status, GoogleBusinessAnalysis.STATUS_FETCHED)

    def test_default_boolean_fields_are_false(self):
        """Domyślnie wszystkie pola boolean są False"""
        analysis = GoogleBusinessAnalysis.objects.create(lead=self.lead)

        self.assertFalse(analysis.has_description)
        self.assertFalse(analysis.has_phone)
        self.assertFalse(analysis.has_website)
        self.assertFalse(analysis.has_hours)
        self.assertFalse(analysis.has_main_image)
        self.assertFalse(analysis.has_posts)
        self.assertFalse(analysis.has_menu_items)
        self.assertFalse(analysis.has_social_links)

    def test_default_nullable_fields_are_none(self):
        """Domyślnie pola z null=True są NULL"""
        analysis = GoogleBusinessAnalysis.objects.create(lead=self.lead)

        self.assertIsNone(analysis.rating)
        self.assertIsNone(analysis.reviews_count)
        self.assertIsNone(analysis.photos_count)
        self.assertIsNone(analysis.posts_count)
        self.assertIsNone(analysis.last_post_date)
        self.assertIsNone(analysis.owner_responses_ratio)

    def test_create_analysis_with_basic_data(self):
        """Tworzy analizę z podstawowymi danymi"""
        analysis = GoogleBusinessAnalysis.objects.create(
            lead=self.lead,
            business_name="Restauracja Włoska",
            rating=4.5,
            reviews_count=120,
            primary_category="Restauracja",
            has_phone=True,
            has_website=True,
            has_description=True,
        )

        self.assertEqual(analysis.business_name, "Restauracja Włoska")
        self.assertEqual(analysis.rating, 4.5)
        self.assertEqual(analysis.reviews_count, 120)
        self.assertTrue(analysis.has_phone)
        self.assertTrue(analysis.has_website)
        self.assertTrue(analysis.has_description)

    def test_analysis_str(self):
        """Sprawdza czy __str__ zawiera nazwę leada"""
        analysis = GoogleBusinessAnalysis.objects.create(lead=self.lead)

        self.assertIn("Jan Kowalski", str(analysis))

    def test_analysis_ordering_newest_first(self):
        """Analizy są posortowane od najnowszej (ordering = -created_at)"""
        first = GoogleBusinessAnalysis.objects.create(lead=self.lead)
        second = GoogleBusinessAnalysis.objects.create(lead=self.lead)

        analyses = list(GoogleBusinessAnalysis.objects.all())

        self.assertEqual(analyses[0], second)
        self.assertEqual(analyses[1], first)

    def test_lead_can_have_multiple_analyses(self):
        """Lead może mieć wiele analiz"""
        GoogleBusinessAnalysis.objects.create(lead=self.lead)
        GoogleBusinessAnalysis.objects.create(lead=self.lead)

        self.assertEqual(GoogleBusinessAnalysis.objects.count(), 2)

    def test_analysis_is_deleted_when_lead_is_deleted(self):
        """Usunięcie leada usuwa też jego analizy (on_delete=CASCADE)"""
        GoogleBusinessAnalysis.objects.create(lead=self.lead)

        self.lead.delete()

        self.assertEqual(GoogleBusinessAnalysis.objects.count(), 0)
