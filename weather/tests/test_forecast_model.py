from datetime import date

from django.test import SimpleTestCase

from weather.ml.dataset import description_to_flags, weathercode_to_flags
from weather.ml.forecast_model import WeatherForecastModel


class TrainServeConsistencyTests(SimpleTestCase):
    """Guards the single biggest risk in this design: training uses WMO
    weather codes to derive condition flags, inference uses OpenWeatherMap's
    text description. If these two mappings ever disagree on an equivalent
    real-world condition, the model would predict on features it was never
    trained to see, silently. This test is the tripwire for that.
    """

    def test_rain_agrees_between_code_and_description(self):
        self.assertEqual(weathercode_to_flags(61)['is_rainy'], description_to_flags('light rain')['is_rainy'])
        self.assertEqual(weathercode_to_flags(80)['is_rainy'], description_to_flags('rain showers')['is_rainy'])
        self.assertEqual(weathercode_to_flags(95)['is_rainy'], description_to_flags('thunderstorm')['is_rainy'])

    def test_snow_agrees_between_code_and_description(self):
        self.assertEqual(weathercode_to_flags(71)['is_snowy'], description_to_flags('light snow')['is_snowy'])

    def test_clear_agrees_between_code_and_description(self):
        self.assertEqual(weathercode_to_flags(0)['is_clear'], description_to_flags('clear sky')['is_clear'])

    def test_cloudy_agrees_between_code_and_description(self):
        self.assertEqual(weathercode_to_flags(3)['is_cloudy'], description_to_flags('overcast clouds')['is_cloudy'])

    def test_non_rainy_conditions_agree(self):
        self.assertEqual(weathercode_to_flags(0)['is_rainy'], description_to_flags('clear sky')['is_rainy'])


class ForecastModelPredictionTests(SimpleTestCase):
    """Loads the actual committed model artifacts (small joblib files) rather
    than retraining in-test. Asserts output shape/ranges, not exact values —
    exact predictions depend on the trained model and shouldn't be hardcoded.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.model = WeatherForecastModel()

    def test_predict_returns_expected_shape(self):
        result = self.model.predict(
            lat=51.5, lon=-0.12, temp=15.0, humidity=70, pressure=1013,
            wind_speed=5.0, description='light rain', date=date(2024, 6, 15),
        )
        self.assertIsNotNone(result)
        self.assertIn('predicted_tomorrow_temp_c', result)
        self.assertIn('rain_probability', result)
        self.assertIn('rain_expected', result)

    def test_rain_probability_is_a_valid_probability(self):
        result = self.model.predict(
            lat=1.35, lon=103.8, temp=28.0, humidity=85, pressure=1008,
            wind_speed=3.0, description='thunderstorm', date=date(2024, 3, 1),
        )
        self.assertGreaterEqual(result['rain_probability'], 0.0)
        self.assertLessEqual(result['rain_probability'], 1.0)

    def test_predicted_temp_is_a_reasonable_value(self):
        result = self.model.predict(
            lat=25.2, lon=55.3, temp=35.0, humidity=30, pressure=1005,
            wind_speed=4.0, description='clear sky', date=date(2024, 7, 1),
        )
        self.assertGreater(result['predicted_tomorrow_temp_c'], -60)
        self.assertLess(result['predicted_tomorrow_temp_c'], 60)