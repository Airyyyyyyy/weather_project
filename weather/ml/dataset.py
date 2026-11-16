"""Shared feature engineering for the weather forecast model.

Both weather/management/commands/train_forecast_model.py (training, using
historical Open-Meteo data) and weather/ml/forecast_model.py (inference,
using a live OpenWeatherMap response) call the functions in this module —
this is what keeps train-time and serve-time features from drifting apart.
"""
import math

# WMO weather codes (used by Open-Meteo's historical archive)
RAINY_CODES = {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99}
SNOWY_CODES = {71, 73, 75, 77, 85, 86}
CLOUDY_CODES = {1, 2, 3, 45, 48}
CLEAR_CODES = {0}

RAIN_THRESHOLD_MM = 1.0  # "measurable precipitation" for the rain classification target

FEATURE_COLUMNS = [
    "lat", "lon", "temp_c", "humidity_pct", "pressure_hpa", "wind_speed_ms",
    "is_rainy", "is_snowy", "is_cloudy", "is_clear",
    "month_sin", "month_cos", "doy_sin", "doy_cos",
]


def weathercode_to_flags(code: int) -> dict:
    """Map an Open-Meteo WMO weather_code to condition flags."""
    code = int(code)
    return {
        "is_rainy": int(code in RAINY_CODES),
        "is_snowy": int(code in SNOWY_CODES),
        "is_cloudy": int(code in CLOUDY_CODES),
        "is_clear": int(code in CLEAR_CODES),
    }


def description_to_flags(description: str) -> dict:
    """Map an OpenWeatherMap text description to the same condition flags."""
    desc = (description or "").lower()
    return {
        "is_rainy": int(any(k in desc for k in ("rain", "drizzle", "thunderstorm"))),
        "is_snowy": int("snow" in desc),
        "is_cloudy": int(any(k in desc for k in ("cloud", "fog", "mist", "overcast", "haze"))),
        "is_clear": int(any(k in desc for k in ("clear", "sun")) and "cloud" not in desc),
    }


def cyclical_date_features(date) -> dict:
    """Cyclical (sin/cos) encodings of month and day-of-year for a date/datetime.date."""
    month = date.month
    day_of_year = date.timetuple().tm_yday
    days_in_year = 366 if _is_leap(date.year) else 365

    return {
        "month_sin": math.sin(2 * math.pi * month / 12),
        "month_cos": math.cos(2 * math.pi * month / 12),
        "doy_sin": math.sin(2 * math.pi * day_of_year / days_in_year),
        "doy_cos": math.cos(2 * math.pi * day_of_year / days_in_year),
    }


def _is_leap(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def build_feature_row(*, lat, lon, temp_c, humidity_pct, pressure_hpa, wind_speed_ms, condition_flags, date) -> dict:
    """Assemble one feature row in FEATURE_COLUMNS order as a dict."""
    row = {
        "lat": lat,
        "lon": lon,
        "temp_c": temp_c,
        "humidity_pct": humidity_pct,
        "pressure_hpa": pressure_hpa,
        "wind_speed_ms": wind_speed_ms,
        **condition_flags,
        **cyclical_date_features(date),
    }
    return {col: row[col] for col in FEATURE_COLUMNS}
