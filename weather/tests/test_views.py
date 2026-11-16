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
    @patch('weather.views.get_current_weather', return_value=FAKE_WEATHER)
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