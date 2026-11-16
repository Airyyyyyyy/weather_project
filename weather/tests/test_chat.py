from django.test import SimpleTestCase

from weather.services.chat import (
    extract_city_from_message,
    generate_enhanced_chat_response,
)

FIXTURE_WEATHER = [
    {
        'city': 'London', 'temperature': 15, 'description': 'light rain',
        'humidity': 80, 'wind_speed': 8, 'feels_like': 13, 'pressure': 1010,
    },
]


class ExtractCityTests(SimpleTestCase):
    def test_finds_mentioned_city(self):
        self.assertEqual(extract_city_from_message('how about london today', ['London']), 'London')

    def test_returns_none_when_no_match(self):
        self.assertIsNone(extract_city_from_message('how about the weather', ['London']))


class ChatResponseTests(SimpleTestCase):
    def test_greeting_with_no_cities(self):
        response = generate_enhanced_chat_response('hello', [], [])
        self.assertIn("haven't added", response)

    def test_greeting_with_cities(self):
        response = generate_enhanced_chat_response('hi', FIXTURE_WEATHER, ['London'])
        self.assertIn('London', response)

    def test_help_lists_options(self):
        response = generate_enhanced_chat_response('help', [], [])
        self.assertIn('clothing', response.lower())

    def test_list_cities(self):
        response = generate_enhanced_chat_response('what cities am I tracking', FIXTURE_WEATHER, ['London'])
        self.assertIn('London', response)

    def test_clothing_question_for_mentioned_city(self):
        response = generate_enhanced_chat_response('what should I wear in london', FIXTURE_WEATHER, ['London'])
        self.assertIn('Clothing recommendation', response)

    def test_weather_question_for_mentioned_city(self):
        response = generate_enhanced_chat_response('what is the weather in london', FIXTURE_WEATHER, ['London'])
        self.assertIn('15', response)

    def test_activity_question(self):
        response = generate_enhanced_chat_response('any activity recommendations', FIXTURE_WEATHER, ['London'])
        self.assertIn('Activity suggestion', response)

    def test_fallback_response_with_cities(self):
        response = generate_enhanced_chat_response('xyzzy nonsense', FIXTURE_WEATHER, ['London'])
        self.assertIn('not sure', response.lower())

    def test_fallback_response_without_cities(self):
        response = generate_enhanced_chat_response('xyzzy nonsense', [], [])
        self.assertIn('add some cities', response.lower())
