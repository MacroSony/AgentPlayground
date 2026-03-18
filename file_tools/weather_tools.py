import httpx
import json

def get_weather(location: str) -> str:
    """Fetches real-time weather information for a given location using Open-Meteo.
    
    Args:
        location: The name of the city or location (e.g., 'London', 'Tokyo').
    """
    try:
        # 1. Geocoding: Get coordinates for the location
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1&language=en&format=json"
        with httpx.Client(timeout=10.0) as client:
            geo_res = client.get(geo_url)
            geo_res.raise_for_status()
            geo_data = geo_res.json()
            
            if not geo_data.get("results"):
                return f"Error: Location '{location}' not found."
            
            result = geo_data["results"][0]
            lat = result["latitude"]
            lon = result["longitude"]
            name = result["name"]
            country = result.get("country", "Unknown")
            
            # 2. Weather: Get forecast for coordinates
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=temperature_2m,relativehumidity_2m,windspeed_10m"
            weather_res = client.get(weather_url)
            weather_res.raise_for_status()
            weather_data = weather_res.json()
            
            current = weather_data["current_weather"]
            temp = current["temperature"]
            wind = current["windspeed"]
            code = current["weathercode"]
            
            # Simple weather code mapping (WMO)
            codes = {
                0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
                45: "Fog", 48: "Depositing rime fog",
                51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
                61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
                71: "Slight snow fall", 73: "Moderate snow fall", 75: "Heavy snow fall",
                77: "Snow grains", 80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
                85: "Slight snow showers", 86: "Heavy snow showers",
                95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
            }
            condition = codes.get(code, "Unknown")
            
            report = (
                f"Weather for {name}, {country}:\n"
                f"- Condition: {condition}\n"
                f"- Temperature: {temp}°C\n"
                f"- Wind Speed: {wind} km/h\n"
                f"- Coordinates: {lat}, {lon}"
            )
            return report
            
    except Exception as e:
        return f"Error fetching weather: {e}"
