from django.test import TestCase
from django.core.exceptions import ValidationError
from ...models import City


class CityModelTest(TestCase):

    def test_create_city_with_all_fields(self):
        """Tworzy miasto ze wszystkimi polami i sprawdza czy dane się zapisały"""
        city = City.objects.create(
            name="Warszawa",
            latitude=52.2297,
            longitude=21.0122
        )

        self.assertEqual(city.name, "Warszawa")
        self.assertEqual(city.latitude, 52.2297)
        self.assertEqual(city.longitude, 21.0122)

    def test_create_city_without_coordinates(self):
        """Tworzy miasto bez koordynatów — latitude i longitude są opcjonalne (null=True)"""
        city = City.objects.create(name="Kraków")

        self.assertEqual(city.name, "Kraków")
        self.assertIsNone(city.latitude)
        self.assertIsNone(city.longitude)

    def test_city_is_saved_in_database(self):
        """Sprawdza czy miasto faktycznie trafia do bazy danych"""
        City.objects.create(name="Gdańsk", latitude=54.3520, longitude=18.6466)

        count = City.objects.count()
        self.assertEqual(count, 1)

    def test_city_name_is_required(self):
        """Nazwa miasta nie może być pustym stringiem"""
        city = City(name="")

        with self.assertRaises(ValidationError):
            city.full_clean()

    def test_city_str(self):
        """Sprawdza czy __str__ zwraca nazwę miasta"""
        city = City.objects.create(name="Wrocław")

        self.assertEqual(str(city), "Wrocław")
