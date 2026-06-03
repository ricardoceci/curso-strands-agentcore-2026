import requests
from strands import Agent, tool
from strands.models.bedrock import BedrockModel
from strands.multiagent.a2a import A2AServer


@tool
def get_weather(city: str, target_date: str) -> dict:
    """Get weather forecast for a city on a specific date.

    Args:
        city: city name, e.g. 'Miami', 'Buenos Aires'.
        target_date: date in YYYY-MM-DD format.

    Returns:
        dict with max temperature and precipitation.
    """
    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1},
    ).json()
    if not geo.get("results"):
        return {"error": f"City '{city}' not found"}
    lat, lon = geo["results"][0]["latitude"], geo["results"][0]["longitude"]
    weather = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat, "longitude": lon,
            "daily": "temperature_2m_max,precipitation_sum",
            "start_date": target_date, "end_date": target_date,
        },
    ).json()
    return {
        "city": city,
        "date": target_date,
        "max_temp_c": weather["daily"]["temperature_2m_max"][0],
        "precipitation_mm": weather["daily"]["precipitation_sum"][0],
    }


weather_agent = Agent(
    name="weather_agent",
    description="Agente experto en clima. Responde a consultas sobre el clima en distintas ciudades y fechas.",
    model=BedrockModel(),
    tools=[get_weather],
    system_prompt="Sos un experto en clima. Responde en espanol.",
    callback_handler=None,
)

server = A2AServer(agent=weather_agent, host="127.0.0.1", port=9010, enable_a2a_compliant_streaming=True)
print("A2A weather server escuchando en http://127.0.0.1:9010")
server.serve()
