from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse


FAKE_WEATHER = {
    'city': 'London', 'temperature': 15.0, 'description': 'light rain',
    'icon': '10d', 'humidity': 80, 'pressure': 1010, 'wind_speed': 8.0,
    'feels_like': 13.0, 'visibility': 10000, 'lat': 51.5, 'lon': -0.12,
}


class IndexViewTests(TestCase):
    def test_get_renders_empty_state_with_no_cities(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No cities added yet')

    @patch('weather.views.city_exists', return_value=True)
    def test_post_adds_city_to_session(self, mock_exists):
        response = self.client.post(reverse('index'), {'name': 'London'})
        self.assertRedirects(response, reverse('index'))
        self.assertEqual(self.client.session['user_cities'], ['London'])

    @patch('weather.views.city_exists', return_value=False)
    def test_post_rejects_unknown_city(self, mock_exists):
        self.client.post(reverse('index'), {'name': 'Notarealplace'})
        self.assertNotIn('user_cities', self.client.session)

    @patch('weather.views.city_exists', return_value=True)
    def test_duplicate_city_is_not_added_twice(self, mock_exists):
        self.client.post(reverse('index'), {'name': 'London'})
        self.client.post(reverse('index'), {'name': 'london'})
        self.assertEqual(self.client.session['user_cities'], ['London'])

    @patch('weather.views.forecast_model.predict', return_value=None)
    @patch('weather.views.get_current_weather_many', return_value=[FAKE_WEATHER])
    @patch('weather.views.city_exists', return_value=True)
    def test_tracked_city_weather_is_displayed(self, mock_exists, mock_weather, mock_forecast):
        self.client.post(reverse('index'), {'name': 'London'})
        response = self.client.get(reverse('index'))
        self.assertContains(response, 'London')
        self.assertContains(response, 'light rain')


class DeleteCityViewTests(TestCase):
    @patch('weather.views.city_exists', return_value=True)
    def test_delete_removes_city_from_session(self, mock_exists):
        self.client.post(reverse('index'), {'name': 'London'})
        self.client.post(reverse('delete_city', args=['London']))
        self.assertEqual(self.client.session['user_cities'], [])

class WeatherApiCacheTests(TestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()

    @patch('weather.services.weather_api._fetch_current_weather', return_value=dict(FAKE_WEATHER))
    def test_second_lookup_uses_cache(self, mock_fetch):
        from weather.services.weather_api import get_current_weather
        get_current_weather('London')
        info = get_current_weather('london')
        self.assertEqual(mock_fetch.call_count, 1)
        self.assertEqual(info['city'], 'london')

    @patch('weather.services.weather_api._fetch_current_weather', return_value=None)
    def test_failed_lookup_is_not_cached(self, mock_fetch):
        from weather.services.weather_api import get_current_weather
        get_current_weather('Nowhere')
        get_current_weather('Nowhere')
        self.assertEqual(mock_fetch.call_count, 2)

    @patch('weather.services.weather_api._fetch_current_weather', side_effect=lambda c: {**FAKE_WEATHER, 'city': c})
    def test_many_preserves_order(self, mock_fetch):
        from weather.services.weather_api import get_current_weather_many
        result = get_current_weather_many(['A', 'B', 'C'])
        self.assertEqual([r['city'] for r in result], ['A', 'B', 'C'])
