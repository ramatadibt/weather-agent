# Standard Library Imports
from datetime import datetime
import time
import uuid
import json
from typing import TypedDict, Sequence, Annotated, Optional, Dict, Any

# Third-Party Library Imports
import streamlit as st
import streamlit_shadcn_ui as ui
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
import markdown
import html


# Weather Data Functions
def fetch_current_weather(lat, lon):
    """Fetch current weather data."""
    url = "https://api.open-meteo.com/v1/forecast"
    
    current_metrics = [
        "temperature_2m", "relative_humidity_2m", 
        "apparent_temperature", "precipitation", 
        "rain", "weathercode", "cloudcover", 
        "windspeed_10m", "winddirection_10m", 
        "pressure_msl", "visibility", "uv_index"
    ]
    
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ",".join(current_metrics),
        "timezone": "auto"
    }
    
    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching current weather: {e}")
        return None

def fetch_forecast_weather(lat, lon):
    """Fetch forecast weather data."""
    url = "https://api.open-meteo.com/v1/forecast"
    
    daily_metrics = [
        "temperature_2m_max", "temperature_2m_min", 
        # "apparent_temperature_max", "apparent_temperature_min",
        "precipitation_sum", 
        # "rain_sum", "showers_sum", 
        # "snowfall_sum", "precipitation_hours",
        "weathercode", "sunrise", "sunset", 
        "windspeed_10m_max", 
        # "windgusts_10m_max", 
        # "uv_index_max"
    ]
    
    hourly_metrics = [
        "temperature_2m", 
        # "relative_humidity_2m", "dew_point_2m", 
        "precipitation_probability",
        "cloudcover", "weathercode", 
        "windspeed_10m",
        #   "winddirection_10m"
    ]
    
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ",".join(daily_metrics),
        "hourly": ",".join(hourly_metrics),
        "timezone": "auto",
        "forecast_days": 7
    }
    
    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching forecast: {e}")
        return None

def fetch_air_quality(lat, lon):
    """Fetch air quality data."""
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    
    hourly_aq_metrics = [
        "pm10", "pm2_5", "european_aqi", "carbon_monoxide",
        "nitrogen_dioxide", "sulphur_dioxide", "ozone"
    ]
    
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ",".join(hourly_aq_metrics),
        "timezone": "auto"
    }
    
    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching air quality: {e}")
        return None

def get_all_weather_data(location_name):
    """Get coordinates, current weather, forecast, and air quality data."""
    try:
        lat, lon = get_coordinates(location_name)
        if lat is None or lon is None:
            return None
            
        current_data = fetch_current_weather(lat, lon)
        forecast_data = fetch_forecast_weather(lat, lon)
        air_quality_data = fetch_air_quality(lat, lon)
        
        return {
            "location": location_name,
            "latitude": lat,
            "longitude": lon,
            "current": current_data,
            "forecast": forecast_data,
            "air_quality": air_quality_data
        }
    except Exception as e:
        st.error(f"Error fetching weather data: {e}")
        return None

# Weather Code to Description Mapping
def get_weather_description(code):
    weather_codes = {
        0: {"description": "Clear sky", "icon": "☀️"},
        1: {"description": "Mainly clear", "icon": "🌤️"},
        2: {"description": "Partly cloudy", "icon": "⛅"},
        3: {"description": "Overcast", "icon": "☁️"},
        45: {"description": "Fog", "icon": "🌫️"},
        48: {"description": "Depositing rime fog", "icon": "🌫️"},
        51: {"description": "Light drizzle", "icon": "🌦️"},
        53: {"description": "Moderate drizzle", "icon": "🌧️"},
        55: {"description": "Dense drizzle", "icon": "🌧️"},
        56: {"description": "Light freezing drizzle", "icon": "🌨️"},
        57: {"description": "Dense freezing drizzle", "icon": "🌨️"},
        61: {"description": "Slight rain", "icon": "🌦️"},
        63: {"description": "Moderate rain", "icon": "🌧️"},
        65: {"description": "Heavy rain", "icon": "🌧️"},
        66: {"description": "Light freezing rain", "icon": "🌨️"},
        67: {"description": "Heavy freezing rain", "icon": "🌨️"},
        71: {"description": "Slight snow fall", "icon": "🌨️"},
        73: {"description": "Moderate snow fall", "icon": "🌨️"},
        75: {"description": "Heavy snow fall", "icon": "❄️"},
        77: {"description": "Snow grains", "icon": "❄️"},
        80: {"description": "Slight rain showers", "icon": "🌦️"},
        81: {"description": "Moderate rain showers", "icon": "🌧️"},
        82: {"description": "Violent rain showers", "icon": "⛈️"},
        85: {"description": "Slight snow showers", "icon": "🌨️"},
        86: {"description": "Heavy snow showers", "icon": "❄️"},
        95: {"description": "Thunderstorm", "icon": "⛈️"},
        96: {"description": "Thunderstorm with slight hail", "icon": "⛈️"},
        99: {"description": "Thunderstorm with heavy hail", "icon": "⛈️"}
    }
    return weather_codes.get(code, {"description": "Unknown", "icon": "❓"})



# Define input schemas
class LocationInput(BaseModel):
    """Input schema for location-to-coordinates tool."""
    location_name: str = Field(
        description="The name of the location to convert to coordinates (e.g., 'New York', 'London')"
    )

class CoordinatesInput(BaseModel):
    """Input schema for weather fetching tool."""
    latitude: float = Field(
        description="Latitude in decimal degrees. Must be between -90 and 90."
    )
    longitude: float = Field(
        description="Longitude in decimal degrees. Must be between -180 and 180."
    )

def get_coordinates(location_name):
    """Convert location name to coordinates."""
    geolocator = Nominatim(user_agent="weather_dashboard_app_v2.0")
    try:
        location = geolocator.geocode(location_name, timeout=20)
        if location:
            print(f"Coordinates found for {location_name}: ({location.latitude}, {location.longitude})")
            return location.latitude, location.longitude
        else:
            print(f"Location '{location_name}' could not be geocoded.")
            return None, None
    except Exception as e:
        print(f"Geocoding failed for '{location_name}': {e}")
        return None, None
