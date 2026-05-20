"""
Weather tool backed by Open-Meteo (no auth required).

Open-Meteo accepts latitude/longitude. We resolve a city name to coordinates
through their free geocoding endpoint first, then fetch the daily forecast.

Docs: https://open-meteo.com/en/docs
"""

from typing import Optional

import requests
from strands import tool

OPEN_METEO_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def _resolve_city(city: str) -> Optional[dict]:
    """Resolve a city name to coordinates using Open-Meteo's geocoder."""
    response = requests.get(
        OPEN_METEO_GEOCODING_URL,
        params={"name": city, "count": 1, "format": "json"},
        timeout=15,
    )
    response.raise_for_status()
    results = response.json().get("results", [])
    return results[0] if results else None


@tool
def get_weather(city: str, target_date: str) -> dict:
    """Get the daily weather forecast for a city on a specific date.

    Use this tool to enrich a flight recommendation with weather context.
    For example: when the user is choosing between two destinations, or
    when they want to know if they should pack an umbrella.

    Args:
        city: City name in any supported language, e.g. "Buenos Aires", "Miami".
        target_date: Date in YYYY-MM-DD format. Must be within the next 16 days.

    Returns:
        A dict with `city`, `country`, `date`, `temperature_max_c`,
        `temperature_min_c`, `precipitation_mm` and `summary`. If the city
        cannot be resolved, returns `{"error": "city_not_found"}`.
    """
    location = _resolve_city(city)
    if not location:
        return {"error": "city_not_found", "city": city}

    response = requests.get(
        OPEN_METEO_FORECAST_URL,
        params={
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
            "start_date": target_date,
            "end_date": target_date,
            "timezone": "auto",
        },
        timeout=15,
    )
    response.raise_for_status()
    daily = response.json().get("daily", {})

    if not daily.get("time"):
        return {
            "error": "no_forecast_for_date",
            "city": city,
            "target_date": target_date,
        }

    return {
        "city": location["name"],
        "country": location.get("country"),
        "date": daily["time"][0],
        "temperature_max_c": daily["temperature_2m_max"][0],
        "temperature_min_c": daily["temperature_2m_min"][0],
        "precipitation_mm": daily["precipitation_sum"][0],
        "summary": _weather_summary(daily["weather_code"][0]),
    }


def _weather_summary(weather_code: int) -> str:
    """Translate a WMO weather code into a short English description."""
    # Subset of the WMO Weather interpretation codes used by Open-Meteo.
    code_map = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        61: "Light rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Light snow",
        73: "Moderate snow",
        80: "Light rain showers",
        95: "Thunderstorm",
    }
    return code_map.get(weather_code, "Unknown")
