"""Fetch real historical daily weather data from Open-Meteo and build the
training CSV used by train_forecast_model. No API key required.

Usage: python manage.py build_training_dataset
"""
import csv
import time
from datetime import date

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from weather.ml.cities import CITIES
from weather.ml.dataset import weathercode_to_flags, RAIN_THRESHOLD_MM

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
START_DATE = "2019-01-01"
END_DATE = "2023-12-31"  # 5 full years, safely within Open-Meteo's archived range
OUTPUT_PATH = settings.BASE_DIR / "weather" / "ml" / "data" / "historical_weather.csv"

DAILY_PARAMS = ",".join([
    "weather_code",
    "temperature_2m_max",
    "temperature_2m_min",
    "rain_sum",
    "wind_speed_10m_max",
    "relative_humidity_2m_mean",
    "surface_pressure_mean",
])


class Command(BaseCommand):
    help = "Fetch historical weather data from Open-Meteo and build the training dataset CSV"

    def handle(self, *args, **options):
        rows = []
        for i, city in enumerate(CITIES, start=1):
            self.stdout.write(f"[{i}/{len(CITIES)}] Fetching {city['name']}...")
            try:
                daily = self._fetch_city(city)
            except requests.RequestException as e:
                self.stderr.write(self.style.WARNING(f"  Skipping {city['name']}: {e}"))
                continue

            rows.extend(self._build_rows(city["name"], daily))
            time.sleep(0.5)

        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "city", "date", "temp_c", "humidity_pct", "pressure_hpa", "wind_speed_ms",
                "is_rainy", "is_snowy", "is_cloudy", "is_clear",
                "y_temp_next", "y_rain_next",
            ])
            writer.writeheader()
            writer.writerows(rows)

        self.stdout.write(self.style.SUCCESS(
            f"Wrote {len(rows)} rows across {len(CITIES)} cities to {OUTPUT_PATH}"
        ))

    def _fetch_city(self, city):
        response = requests.get(
            ARCHIVE_URL,
            params={
                "latitude": city["lat"],
                "longitude": city["lon"],
                "start_date": START_DATE,
                "end_date": END_DATE,
                "daily": DAILY_PARAMS,
                "wind_speed_unit": "ms",
                "timezone": "UTC",
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["daily"]

    def _build_rows(self, city_name, daily):
        rows = []
        n = len(daily["time"])
        for t in range(n - 1):  # last day has no "tomorrow" target available
            tmax, tmin = daily["temperature_2m_max"][t], daily["temperature_2m_min"][t]
            next_tmax, next_tmin = daily["temperature_2m_max"][t + 1], daily["temperature_2m_min"][t + 1]

            if None in (tmax, tmin, next_tmax, next_tmin):
                continue  # occasional missing days in the archive

            flags = weathercode_to_flags(daily["weather_code"][t])
            next_rain = daily["rain_sum"][t + 1]

            rows.append({
                "city": city_name,
                "date": daily["time"][t],
                "temp_c": (tmax + tmin) / 2,
                "humidity_pct": daily["relative_humidity_2m_mean"][t],
                "pressure_hpa": daily["surface_pressure_mean"][t],
                "wind_speed_ms": daily["wind_speed_10m_max"][t],
                "is_rainy": flags["is_rainy"],
                "is_snowy": flags["is_snowy"],
                "is_cloudy": flags["is_cloudy"],
                "is_clear": flags["is_clear"],
                "y_temp_next": (next_tmax + next_tmin) / 2,
                "y_rain_next": int((next_rain or 0) >= RAIN_THRESHOLD_MM),
            })
        return rows
