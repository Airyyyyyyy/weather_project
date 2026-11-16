from django.test import SimpleTestCase

from weather.services.recommendations import (
    generate_rule_based_insight,
    generate_smart_alerts,
    get_activity_suggestion,
    get_clothing_advice,
)


class ClothingAdviceTests(SimpleTestCase):
    def test_hot_clear_day(self):
        advice = get_clothing_advice(32, 'clear sky')
        self.assertIn('Lightweight', advice)
        self.assertIn('sunscreen', advice.lower())

    def test_cold_snowy_day(self):
        advice = get_clothing_advice(-5, 'light snow')
        self.assertIn('winter', advice.lower())

    def test_rainy_conditions_add_waterproof_advice(self):
        advice = get_clothing_advice(18, 'light rain')
        self.assertIn('Waterproof', advice)

    def test_windy_conditions_add_wind_advice(self):
        advice = get_clothing_advice(18, 'windy')
        self.assertIn('Wind-resistant', advice)


class ActivitySuggestionTests(SimpleTestCase):
    def test_rain_suggests_indoor(self):
        suggestion = get_activity_suggestion(20, 'moderate rain')
        self.assertIn('indoor', suggestion.lower())

    def test_hot_clear_suggests_water_activities(self):
        suggestion = get_activity_suggestion(28, 'clear sky')
        self.assertIn('water', suggestion.lower())

    def test_mild_suggests_outdoor(self):
        suggestion = get_activity_suggestion(18, 'clear sky')
        self.assertIn('outdoor', suggestion.lower())

    def test_cold_suggests_indoor(self):
        suggestion = get_activity_suggestion(-2, 'clear sky')
        self.assertIn('indoor', suggestion.lower())


class RuleBasedInsightTests(SimpleTestCase):
    def test_mentions_city_name(self):
        insight = generate_rule_based_insight('Berlin', 22, 'clear sky', 50, 5)
        self.assertIn('Berlin', insight)

    def test_high_humidity_mentioned(self):
        insight = generate_rule_based_insight('Miami', 30, 'clear sky', 90, 5)
        self.assertIn('humidity', insight.lower())

    def test_high_wind_mentioned(self):
        insight = generate_rule_based_insight('Chicago', 15, 'clear sky', 50, 20)
        self.assertIn('windy', insight.lower())


class SmartAlertsTests(SimpleTestCase):
    def test_extreme_heat_triggers_warning(self):
        alerts = generate_smart_alerts([{
            'city': 'Phoenix', 'temperature': 40, 'description': 'clear sky',
            'humidity': 20, 'wind_speed': 2,
        }])
        warning_alerts = [a for a in alerts if a['type'] == 'warning']
        self.assertTrue(any('heat' in a['alert'].lower() for a in warning_alerts))

    def test_no_alerts_for_mild_conditions(self):
        alerts = generate_smart_alerts([{
            'city': 'London', 'temperature': 18, 'description': 'clear sky',
            'humidity': 50, 'wind_speed': 5,
        }])
        self.assertEqual(alerts, [])

    def test_thunderstorm_triggers_warning(self):
        alerts = generate_smart_alerts([{
            'city': 'Miami', 'temperature': 25, 'description': 'thunderstorm',
            'humidity': 60, 'wind_speed': 5,
        }])
        self.assertTrue(any(a['type'] == 'warning' for a in alerts))
