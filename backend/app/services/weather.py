import requests
from datetime import datetime
from typing import Any

CHICAGO_COORDS = (41.8781, -87.6298)
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_CODE_DESCRIPTIONS = {
    0: "clear skies",
    1: "mostly clear skies",
    2: "partly cloudy skies",
    3: "overcast conditions",
    45: "fog",
    48: "dense fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "heavy drizzle",
    56: "freezing drizzle",
    57: "heavy freezing drizzle",
    61: "light rain",
    63: "moderate rain",
    65: "heavy rain",
    66: "freezing rain",
    67: "heavy freezing rain",
    71: "light snow",
    73: "moderate snow",
    75: "heavy snow",
    77: "snow grains",
    80: "light rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    85: "light snow showers",
    86: "heavy snow showers",
    95: "thunderstorms",
    96: "thunderstorms with hail",
    99: "severe thunderstorms with hail",
}


def _format_observation_time(timestamp: str | None) -> str | None:
    if not timestamp:
        return None

    try:
        observation = datetime.fromisoformat(timestamp)
    except ValueError:
        return None

    return observation.strftime("%I:%M %p").lstrip("0").lower()


def _describe_weather_code(code: Any) -> str:
    if isinstance(code, int):
        return WEATHER_CODE_DESCRIPTIONS.get(code, "current conditions")
    return "current conditions"


def get_chicago_weather_summary() -> str:
    params = {
        "latitude": CHICAGO_COORDS[0],
        "longitude": CHICAGO_COORDS[1],
        "current_weather": "true",
        "temperature_unit": "fahrenheit",
        "windspeed_unit": "mph",
        "precipitation_unit": "inch",
        "timezone": "America/Chicago",
    }

    try:
        response = requests.get(OPEN_METEO_URL, params=params, timeout=5)
        response.raise_for_status()
    except requests.RequestException:
        return (
            "I'm having trouble checking Chicago's weather right now. "
            "Please try again in a moment."
        )

    payload = response.json()
    current_weather = payload.get("current_weather")

    if not current_weather:
        return "Weather data for Chicago is temporarily unavailable."

    temperature = current_weather.get("temperature")
    windspeed = current_weather.get("windspeed")
    weather_code = current_weather.get("weathercode")
    observation_time = _format_observation_time(current_weather.get("time"))

    description = _describe_weather_code(weather_code)

    pieces = [
        "Here's the latest weather for Chicago, IL",
    ]

    if observation_time:
        pieces[0] += f" (updated around {observation_time})"
    pieces[0] += ": "

    if temperature is not None:
        pieces.append(f"{temperature:.0f}°F")

    pieces.append(f"with {description}.")

    if windspeed is not None:
        pieces.append(f"Winds around {windspeed:.0f} mph.")

    return " ".join(pieces)
