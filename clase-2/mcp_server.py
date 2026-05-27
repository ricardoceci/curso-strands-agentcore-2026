"""
Custom MCP server that wraps the Duffel sandbox API.

Exposes the three MCP primitives:
  Tools:     search_flights, get_offer_details, get_weather
  Resources: airports://list  — static IATA airport catalogue
  Prompts:   planificar_viaje — template to plan a trip end-to-end

Run standalone for debugging:
    python mcp_server.py --http

In production it is started by the agent as a stdio subprocess, so we
avoid HTTP, ports and auth between agent and server.
"""

import json
import os
from typing import Optional

import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

DUFFEL_API_BASE_URL = "https://api.duffel.com"
DUFFEL_API_VERSION = "v2"

mcp = FastMCP("duffel-travel")


def _duffel_headers() -> dict:
    """Build the headers required by every Duffel request."""
    api_key = os.environ.get("DUFFEL_API_KEY")
    if not api_key:
        raise RuntimeError("DUFFEL_API_KEY is not set in the environment.")
    return {
        "Authorization": f"Bearer {api_key}",
        "Duffel-Version": DUFFEL_API_VERSION,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


@mcp.tool()
def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    cabin_class: str = "economy",
    adults: int = 1,
    max_results: int = 5,
) -> dict:
    """Search for one-way flights using the Duffel sandbox API.

    Args:
        origin: Origin airport IATA code (3 letters).
        destination: Destination airport IATA code (3 letters).
        departure_date: Date in YYYY-MM-DD format.
        cabin_class: economy | premium_economy | business | first.
        adults: Number of adult passengers.
        max_results: Maximum offers to return, ordered by price ascending.
    """
    payload = {
        "data": {
            "slices": [
                {
                    "origin": origin.upper(),
                    "destination": destination.upper(),
                    "departure_date": departure_date,
                }
            ],
            "passengers": [{"type": "adult"} for _ in range(adults)],
            "cabin_class": cabin_class,
        }
    }
    response = requests.post(
        f"{DUFFEL_API_BASE_URL}/air/offer_requests",
        headers=_duffel_headers(),
        params={"return_offers": "true"},
        json=payload,
        timeout=30,
    )
    if response.status_code >= 400:
        return {
            "error": "duffel_request_failed",
            "status_code": response.status_code,
            "details": response.text[:500],
        }

    data = response.json().get("data", {})
    offers = data.get("offers", [])
    offers_sorted = sorted(offers, key=lambda o: float(o.get("total_amount", 1e9)))
    return {
        "offer_request_id": data.get("id"),
        "offers": [_simplify_offer(o) for o in offers_sorted[:max_results]],
    }


@mcp.tool()
def get_offer_details(offer_id: str) -> dict:
    """Retrieve full details for a previously returned Duffel offer.

    Args:
        offer_id: The Duffel offer identifier (starts with "off_").
    """
    response = requests.get(
        f"{DUFFEL_API_BASE_URL}/air/offers/{offer_id}",
        headers=_duffel_headers(),
        timeout=30,
    )
    if response.status_code >= 400:
        return {
            "error": "duffel_request_failed",
            "status_code": response.status_code,
            "details": response.text[:500],
        }
    return response.json().get("data", {})


def _simplify_offer(offer: dict) -> dict:
    """Reduce a Duffel offer to the minimum fields the agent needs."""
    first_slice = offer.get("slices", [{}])[0]
    segments = first_slice.get("segments", [])
    first_segment: Optional[dict] = segments[0] if segments else None
    last_segment: Optional[dict] = segments[-1] if segments else None
    return {
        "offer_id": offer.get("id"),
        "total_amount": offer.get("total_amount"),
        "currency": offer.get("total_currency"),
        "airline": offer.get("owner", {}).get("name"),
        "departure_time": first_segment.get("departing_at") if first_segment else None,
        "arrival_time": last_segment.get("arriving_at") if last_segment else None,
        "duration": first_slice.get("duration"),
        "stops": max(0, len(segments) - 1),
    }

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

@mcp.tool()
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


# ---------------------------------------------------------------------------
# Resource: lista de aeropuertos con código IATA
# Los recursos exponen datos estáticos como contexto — sin ejecutar nada.
# El cliente los puede leer con: read_resource("airports://list")
# ---------------------------------------------------------------------------

AIRPORTS = [
    {"iata": "EZE", "city": "Buenos Aires", "name": "Ministro Pistarini International", "country": "Argentina"},
    {"iata": "AEP", "city": "Buenos Aires", "name": "Jorge Newbery Airpark", "country": "Argentina"},
    {"iata": "COR", "city": "Córdoba", "name": "Ingeniero Taravella International", "country": "Argentina"},
    {"iata": "MDZ", "city": "Mendoza", "name": "El Plumerillo International", "country": "Argentina"},
    {"iata": "SCL", "city": "Santiago", "name": "Arturo Merino Benítez International", "country": "Chile"},
    {"iata": "GRU", "city": "São Paulo", "name": "Guarulhos International", "country": "Brazil"},
    {"iata": "GIG", "city": "Rio de Janeiro", "name": "Galeão International", "country": "Brazil"},
    {"iata": "BOG", "city": "Bogotá", "name": "El Dorado International", "country": "Colombia"},
    {"iata": "LIM", "city": "Lima", "name": "Jorge Chávez International", "country": "Peru"},
    {"iata": "MIA", "city": "Miami", "name": "Miami International", "country": "United States"},
    {"iata": "JFK", "city": "New York", "name": "John F. Kennedy International", "country": "United States"},
    {"iata": "LAX", "city": "Los Angeles", "name": "Los Angeles International", "country": "United States"},
    {"iata": "ORD", "city": "Chicago", "name": "O'Hare International", "country": "United States"},
    {"iata": "MAD", "city": "Madrid", "name": "Adolfo Suárez Madrid-Barajas", "country": "Spain"},
    {"iata": "LHR", "city": "London", "name": "Heathrow Airport", "country": "United Kingdom"},
    {"iata": "CDG", "city": "Paris", "name": "Charles de Gaulle Airport", "country": "France"},
    {"iata": "FRA", "city": "Frankfurt", "name": "Frankfurt Airport", "country": "Germany"},
    {"iata": "MEX", "city": "Mexico City", "name": "Benito Juárez International", "country": "Mexico"},
    {"iata": "CUN", "city": "Cancún", "name": "Cancún International", "country": "Mexico"},
    {"iata": "NRT", "city": "Tokyo", "name": "Narita International", "country": "Japan"},
]


@mcp.resource("airports://list")
def list_airports() -> str:
    """Lista de aeropuertos soportados con sus códigos IATA.

    Usá este resource para resolver nombres de ciudades a códigos IATA antes
    de llamar a search_flights.
    """
    return json.dumps(AIRPORTS, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Prompt: planificar un viaje completo
# Los prompts son templates reutilizables con variables — el cliente los
# instancia con parámetros concretos y los inyecta como contexto al modelo.
# ---------------------------------------------------------------------------

@mcp.prompt()
def planificar_viaje(origen: str, destino: str, fecha_ida: str, incluir_clima: str = "si") -> str:
    """Template para planificar un viaje: busca vuelos y opcionalmente el clima.

    Args:
        origen: Ciudad o código IATA de origen. Ej: "Buenos Aires" o "EZE".
        destino: Ciudad o código IATA de destino. Ej: "Miami" o "MIA".
        fecha_ida: Fecha de salida en formato YYYY-MM-DD.
        incluir_clima: "si" para agregar pronóstico del clima en destino.
    """
    clima_step = (
        f"\n3. Consultá el clima en {destino} para el {fecha_ida} con get_weather."
        if incluir_clima.lower() == "si"
        else ""
    )
    return (
        f"Planificá un viaje de {origen} a {destino} para el {fecha_ida}.\n\n"
        f"1. Si no tenés los códigos IATA, consultá el resource airports://list para resolverlos.\n"
        f"2. Buscá vuelos con search_flights usando los códigos IATA correctos.{clima_step}\n\n"
        f"Presentá las opciones con aerolínea, horarios, duración, escalas y precio."
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--http", action="store_true", help="Run with StreamableHTTP transport (for notebooks / external clients)")
    parser.add_argument("--port", type=int, default=8002)
    args = parser.parse_args()

    if args.http:
        mcp.settings.port = args.port
        mcp.run(transport="streamable-http")
    else:
        # Default: stdio, used by the agent as a managed subprocess.
        mcp.run()
