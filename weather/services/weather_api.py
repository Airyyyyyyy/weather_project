import logging
from concurrent.futures import ThreadPoolExecutor

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

OWM_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
REQUEST_TIMEOUT = 10
CACHE_SECONDS = 600  # reuse a city's weather for 10 minutes
MAX_WORKERS = 8

# One shared session reuses the HTTPS connection instead of re-handshaking every call.
_session = requests.Session()


def get_current_weather(city_name: str) -> dict | None:
    """Current weather for a city, cached briefly. Returns None on any failure."""
    key = "owm:" + city_name.strip().lower()
    cached = cache.get(key)
    if cached is not None:
        return {**cached, "city": city_name}

    info = _fetch_current_weather(city_name)
    if info is not None:
        cache.set(key, info, CACHE_SECONDS)
    return info


def get_current_weather_many(city_names: list[str]) -> list[dict | None]:
    """Fetch several cities in parallel, preserving input order."""
    if len(city_names) <= 1:
        return [get_current_weather(c) for c in city_names]
    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(city_names))) as pool:
        return list(pool.map(get_current_weather, city_names))


def _fetch_current_weather(city_name: str) -> dict | None:
    """Fetch current weather for a city from OpenWeatherMap. Returns None on any failure."""
    try:
        response = _session.get(
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
