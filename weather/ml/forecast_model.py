"""Real ML weather forecasting: predicts tomorrow's temperature and rain
likelihood from today's conditions, using models trained on real historical
data (see weather/management/commands/train_forecast_model.py).
"""
import json
import logging

import joblib
import pandas as pd
from django.conf import settings

from .dataset import FEATURE_COLUMNS, build_feature_row, description_to_flags

logger = logging.getLogger(__name__)

ARTIFACTS_DIR = settings.BASE_DIR / "weather" / "ml" / "artifacts"


class WeatherForecastModel:
    def __init__(self):
        self._temp_regressor = None
        self._rain_classifier = None
        self._feature_columns = FEATURE_COLUMNS
        self._loaded = False

    def _load(self):
        if self._loaded:
            return True
        try:
            self._temp_regressor = joblib.load(ARTIFACTS_DIR / "temp_regressor.joblib")
            self._rain_classifier = joblib.load(ARTIFACTS_DIR / "rain_classifier.joblib")
            self._feature_columns = json.loads((ARTIFACTS_DIR / "feature_columns.json").read_text())
            self._loaded = True
            return True
        except (FileNotFoundError, OSError, ValueError):
            logger.exception("Failed to load forecast model artifacts")
            return False

    def predict(self, *, lat, lon, temp, humidity, pressure, wind_speed, description, date):
        """Predict tomorrow's weather from today's conditions. Returns None on any failure."""
        if not self._load():
            return None

        try:
            feature_row = build_feature_row(
                lat=lat, lon=lon, temp_c=temp, humidity_pct=humidity,
                pressure_hpa=pressure, wind_speed_ms=wind_speed,
                condition_flags=description_to_flags(description), date=date,
            )
            X = pd.DataFrame([feature_row], columns=self._feature_columns)

            predicted_temp = float(self._temp_regressor.predict(X)[0])
            rain_probability = float(self._rain_classifier.predict_proba(X)[0][1])

            return {
                "predicted_tomorrow_temp_c": round(predicted_temp, 1),
                "rain_probability": round(rain_probability, 2),
                "rain_expected": rain_probability >= 0.5,
            }
        except Exception:
            logger.exception("Forecast prediction failed")
            return None


# Module-level singleton, loaded lazily on first predict() call.
forecast_model = WeatherForecastModel()