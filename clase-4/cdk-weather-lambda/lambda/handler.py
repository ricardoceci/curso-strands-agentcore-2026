"""
Lambda handler for the get_weather tool exposed via AgentCore Gateway.

AgentCore Gateway invoca esta función con:
  event   — dict plano con los parámetros del tool: {"city": "...", "target_date": "..."}
  context — context.client_context.custom contiene metadatos del gateway:
              bedrockAgentCoreToolName = "<target_name>___get_weather"
              bedrockAgentCoreGatewayId, bedrockAgentCoreTargetId, ...

Solo usa stdlib (urllib) para no necesitar bundling ni capas adicionales.
"""

import json
import urllib.parse
import urllib.request
from typing import Any

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Separador que AgentCore usa entre target_name y tool_name.
DELIMITER = "___"

WMO_CODES: dict[int, str] = {
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


def _http_get(base_url: str, params: dict) -> dict:
    query = "&".join(
        f"{urllib.parse.quote(str(k))}={urllib.parse.quote(str(v), safe=',')}"
        for k, v in params.items()
    )
    url = f"{base_url}?{query}"
    with urllib.request.urlopen(url, timeout=15) as resp:
        return json.loads(resp.read().decode())


def _resolve_city(city: str) -> dict | None:
    data = _http_get(GEOCODING_URL, {"name": city, "count": 1, "format": "json"})
    results = data.get("results", [])
    return results[0] if results else None


def _get_weather(city: str, target_date: str) -> dict:
    location = _resolve_city(city)
    if not location:
        return {"error": "city_not_found", "city": city}

    data = _http_get(
        FORECAST_URL,
        {
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
            "start_date": target_date,
            "end_date": target_date,
            "timezone": "auto",
        },
    )
    daily = data.get("daily", {})
    if not daily.get("time"):
        return {"error": "no_forecast_for_date", "city": city, "target_date": target_date}

    return {
        "city": location["name"],
        "country": location.get("country"),
        "date": daily["time"][0],
        "temperature_max_c": daily["temperature_2m_max"][0],
        "temperature_min_c": daily["temperature_2m_min"][0],
        "precipitation_mm": daily["precipitation_sum"][0],
        "summary": WMO_CODES.get(daily["weather_code"][0], "Unknown"),
    }


def lambda_handler(event: dict, context: Any) -> dict:
    # AgentCore prefija el tool name con el nombre del target: "weather-tool___get_weather".
    # Lo quitamos para obtener el nombre limpio definido en tool_schema.json.
    raw_tool_name: str = context.client_context.custom.get("bedrockAgentCoreToolName", "")
    tool_name = (
        raw_tool_name[raw_tool_name.index(DELIMITER) + len(DELIMITER):]
        if DELIMITER in raw_tool_name
        else raw_tool_name
    )

    if tool_name == "get_weather":
        return _get_weather(
            city=event["city"],
            target_date=event["target_date"],
        )

    return {"error": "unknown_tool", "tool": tool_name}
