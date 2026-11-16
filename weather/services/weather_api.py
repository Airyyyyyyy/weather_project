import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

OWM_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
REQUEST_TIMEOUT = 10


def get_current_weather(city_name: str) -> dict | None:
    """Fetch current weather for a city from OpenWeatherMap. Returns None on any failure."""
    try:
        response = requests.get(
            OWM_BASE_URL,
            params={
                "q": city_name,
                "units": "metric",
                "appid": settings.OPENWEATHER_API_KEY,
            },
            timeout=REQUEST_TIMEOUT,
        )
        data = response.json()
    except requests.RequestException:
        logger.exception("Failed to fetch weather for %s", city_name)
        return None

    if data.get("cod") != 200 or "main" not in data:
        return None

    return {
        "city": city_name,
        "temperature": data["main"]["temp"],
        "description": data["weather"][0]["description"],
        "icon": data["weather"][0]["icon"],
        "humidity": data["main"]["humidity"],
        "pressure": data["main"]["pressure"],
        "wind_speed": data["wind"]["speed"],
        "feels_like": data["main"]["feels_like"],
        "visibility": data.get("visibility", "N/A"),
        "lat": data["coord"]["lat"],
        "lon": data["coord"]["lon"],
    }


def city_exists(city_name: str) -> bool:
    """Check whether a city name resolves to a real OpenWeatherMap location."""
    return get_current_weather(city_name) is not None
