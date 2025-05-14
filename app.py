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
import os 
os.environ['GROQ_API_KEY'] = st.secrets["GROQ_API_KEY"]


# LangChain and LangGraph Imports
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.messages import SystemMessage
from langchain_core.tools import BaseTool, tool
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

# from langchain.tools import tool
from langchain.prompts import PromptTemplate

import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# Page configuration
st.set_page_config(
        page_title="Weather Dashboard",
        page_icon="🌤️",
        layout="wide",
        initial_sidebar_state="collapsed"
    )


current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, '.streamlit', 'config.yaml')
with open(config_path) as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    auto_hash=False  # Important since you've pre-hashed the passwords
)

name, authentication_status, username = authenticator.login('main')

if authentication_status:


    # Custom CSS
    st.markdown("""
    <style>
        .main {
            background-color: #1E293B;
            color: #E0E0E0;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            justify-content: center;
            width: 100%;
            background-color: #273c75;
            padding: 10px 0;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            border-radius: 4px 4px 0px 0px;
            gap: 1px;
            padding: 10px 20px;
            background-color: #273c75;
            color: #E0E0E0;
            min-width: 120px;
            text-align: center;
            flex-grow: 1;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background-color: #34495E;
            color: #FFFFFF;
        }
        div[data-testid="stVerticalBlock"] > div:has(div.element-container) {
            background-color: #1E293B;
            padding: 0.5rem;  /* Reduced padding to minimize height */
            border-radius: 10px;
        }
        div.stMetric {
            background-color: #283B5B;
            padding: 15px;
            border-radius: 8px;
            color: #E0E0E0;
        }
        div.chat-message {
            padding: 1.5rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            display: flex;
        }
        div.chat-message.user {
            background-color: #475569;
            color: #E0E0E0;
        }
        div.chat-message.bot {
            background-color: #334155;
            color: #E0E0E0;
        }
        div.chat-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            object-fit: cover;
            margin-right: 1rem;
        }
        div.chat-content {
            flex-grow: 1;
            color: #E0E0E0;
        }
        div.chat-container {
            height: 400px;
            overflow-y: auto;
            padding: 1rem;
            border-radius: 0.5rem;
            background-color: #1E293B;
            color: #E0E0E0;
        }
        .avatar-img {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            object-fit: cover;
        }
        div.weather-card {
            background-color: #273c75;
            border-radius: 10px;
            padding: 20px;
            color: #E0E0E0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .daily-forecast-card {
            background-color: #34495E;
            border-radius: 8px;
            padding: 10px;
            text-align: center;
            transition: transform 0.2s;
            color: #E0E0E0;
        }
        .daily-forecast-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 10px rgba(0, 0, 0, 0.2);
        }
        .hourly-forecast-card {
            background-color: #34495E;
            border-radius: 8px;
            padding: 10px;
            text-align: center;
            transition: transform 0.2s;
            color: #E0E0E0;
        }
        .hourly-forecast-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 10px rgba(0, 0, 0, 0.2);
        }
        .pollutant-card {
            background-color: #34495E;
            padding: 10px;
            border-radius: 10px;
            text-align: center;
            color: #E0E0E0;
            margin: 5px;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #FFFFFF;
        }
        .metric-label {
            font-size: 14px;
            color: #D3D3D3;
        }
        .pollutant-value {
            font-size: 22px;
            font-weight: bold;
            color: #FFFFFF;
        }
        .forecast-value {
            font-size: 20px;
            font-weight: bold;
            color: #FFFFFF;
        }
        .forecast-label {
            font-size: 14px;
            color: #D3D3D3;
        }
        .section-title {
            font-size: 20px;
            font-weight: 500;
            margin-bottom: 15px;
            color: #F5F6FA;
        }
        .location-title {
            font-size: 24px;
            font-weight: bold;
            color: #E0E0E0;
            margin-bottom: 10px;
        }
        input.st-text-input > div > input {
            color: #E0E0E0;  /* Ensure text is visible */
            background-color: #2A4066;
            height: 2rem;  /* Consistent height */
            padding: 0.25rem 0.5rem;  /* Reduced padding for compactness */
            vertical-align: middle;  /* Align with button */
            line-height: normal;  /* Reset line-height to prevent vertical text */
            white-space: nowrap;  /* Prevent text wrapping */
            width: 100%;  /* Ensure input takes full available width */
            font-size: 14px;  /* Reduce font size if needed */
        }
        input.st-text-input > div > input::placeholder {
            color: #D3D3D3;  /* Improved contrast for placeholder */
            opacity: 1;     /* Ensure placeholder is fully visible */
            font-size: 14px;  /* Match input font size */
        }
        .stButton > button {
            height: 2rem;  /* Match input height */
            padding: 0 1rem;  /* Consistent padding */
            vertical-align: middle;  /* Align with input */
            line-height: 2rem;  /* Center text vertically */
            font-size: 14px;  /* Match input font size */
        }
                .main-weather-card {
        display: flex;
        flex-direction: column;
        background-color: #273c75;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 15px;
    }

    .weather-primary {
        display: flex;
        align-items: center;
        margin-bottom: 5px;
    }

    .temperature-large {
        font-size: 48px;
        font-weight: bold;
        color: #FFFFFF;
        margin-right: 15px;
    }

    .weather-icon-large {
        font-size: 42px;
        margin-left: 10px;
    }

    .weather-description {
        display: flex;
        flex-direction: column;
    }

    .weather-condition {
        font-size: 20px;
        font-weight: 500;
        color: #E0E0E0;
    }

    .feels-like {
        font-size: 18px;
        color: #D3D3D3;
        margin-top: 4px;
    }

    .highlight-metrics-container {
        display: flex;
        flex-direction: column;
        gap: 10px;
    }

    .highlight-metric-card {
        display: flex;
        align-items: center;
        background-color: #34495E;
        border-radius: 8px;
        padding: 10px;
    }

    .metric-icon {
        font-size: 24px;
        margin-right: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: 40px;
    }

    .metric-details {
        display: flex;
        flex-direction: column;
    }

    .metric-value {
        font-size: 20px;
        font-weight: bold;
        color: #FFFFFF;
    }

    .metric-name {
        font-size: 20px; color: #1a1a1a; font-weight: 700;
    }

    .section-subtitle {
        font-size: 18px;
        font-weight: 500;
        color: #E0E0E0;
        margin: 15px 0 10px 0;
    }

    .metric-card {
        background-color: #34495E;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
        height: 100%;
        transition: transform 0.2s;
    }

    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 5px 10px rgba(0, 0, 0, 0.2);
    }

    .metric-card-icon {
        font-size: 28px;
        margin-bottom: 5px;
    }

    .metric-card-label {
        font-size: 14px;
        color: #D3D3D3;
        margin-bottom: 5px;
    }

    .metric-card-value {
        font-size: 20px;
        font-weight: bold;
        color: #FFFFFF;
    }

    .metric-card-sublabel {
        font-size: 12px;
        color: #D3D3D3;
        margin-top: 3px;
    }
    .chart-title {
        font-size: 22px;
        font-weight: 600;
        color: #FFFFFF;
        text-align: center;
        margin: 15px 0;
        background-color: rgba(52, 73, 94, 0.7);
        padding: 8px;
        border-radius: 6px;
    }
    .weather-details-container {
        background-color: #2C3E50;
        padding: 15px;
        border-radius: 10px;
        margin-top: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    } 
        .highlight-metric-card:nth-child(1) {
        background: linear-gradient(135deg, #E69500  30%,  #E6C200 60%);
        border: 1px solid rgba(230, 194, 0, 0.2);
    }

    .highlight-metric-card:nth-child(2) {
        background: linear-gradient(135deg, #E0533F 30%,  #753434  90%);
        border: 1px solid rgba(117, 0, 0, 0.2);
        }
        .highlight-metrics-container {
            gap: 15px;  /* Increased gap between cards */
        }
        .highlight-metric-card {
            min-height: 90px;  /* Fixed minimum height */
            padding: 15px;  /* Increased padding */
        }
        .main-weather-card {
            min-height: 210px;  /* Fixed height for main card */
        }
        /* Adjust icon sizes for better balance */
        .metric-icon {
            font-size: 28px;
            min-width: 45px;
        }
        .metric-value {
            font-size: 20px;
        }       
    </style>
    """, unsafe_allow_html=True)

    # Geocoding Functions
    def get_coordinates(location_name):
        """Convert location name to coordinates."""
        geolocator = Nominatim(user_agent="weather_dashboard_app_v2.0")
        try:
            location = geolocator.geocode(location_name, timeout=20)
            if location:
                print(f"Coordinates found for {location_name}: ({location.latitude}, {location.longitude})")
                return location.latitude, location.longitude
            else:
                st.error(f"Location '{location_name}' could not be geocoded.")
                return None, None
        except Exception as e:
            st.error(f"Geocoding failed for '{location_name}': {e}")
            return None, None

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

    # Keep your existing get_coordinates function as is
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
            print(f"Error fetching current weather: {e}")
            return None

    @tool(args_schema=LocationInput)
    def get_coordinates_tool(location_name: str) -> dict:
        """
        Get latitude and longitude for a given location name using geocoding.
        
        This tool MUST be used first before fetching weather data.
        Always use this tool when the user provides a new location name.
        
        Parameters:
        - location_name (str): The name of the location (e.g., "New York", "London").
        
        Returns:
        - dict: A dictionary containing:
            - latitude (float): The latitude of the location in degrees.
            - longitude (float): The longitude of the location in degrees.
            - error (str, optional): Error message if the location cannot be found.
        """
        print(f"Tool is calling get_coordinates for '{location_name}'...")
        
        # Simulate the coordinate retrieval
        lat, lon = get_coordinates(location_name)
        if lat is None or lon is None:
            return {"error": f"Could not find coordinates for {location_name}"}
        return {"latitude": lat, "longitude": lon}

    @tool(args_schema=CoordinatesInput)
    def fetch_current_weather_tool(latitude: float, longitude: float) -> dict:
        """
        Fetches the current weather for a specific geographic location.
        
        IMPORTANT: This tool can only be used AFTER getting coordinates with the get_coordinates_tool.
        
        Parameters:
        - latitude (float): Latitude in decimal degrees. Must be between -90 and 90.
        - longitude (float): Longitude in decimal degrees. Must be between -180 and 180.
        
        Returns:
        - dict: Weather data for the specified location
        """
        print(f"Tool is calling fetch_current_weather with coordinates: {latitude}, {longitude}")
        
        # Fetch the weather data
        data = fetch_current_weather(latitude, longitude)
        if not data:
            return {"error": "Weather data unavailable"}
        
        try:
            processed = {
                'location': {
                    'latitude': data['latitude'],
                    'longitude': data['longitude'],
                    'timezone': data['timezone']
                },
                'timestamp': data['current']['time'],
                'metrics': {}
            }

            units = data['current_units']
            for metric, value in data['current'].items():
                if metric in ['time', 'interval']:
                    continue
                    
                processed['metrics'][f"{metric} ({units[metric]})" 
                                if units.get(metric) 
                                else metric] = value
            return processed
        
        except KeyError as e:
            return {"error": f"Data format error: {str(e)}"}

    # Create a single weather tool that handles the whole process
    class WeatherRequest(BaseModel):
        """Input schema for the combined weather tool."""
        location: str = Field(
            description="The name of the location to get weather for (e.g., 'New York', 'London')"
        )

    @tool(args_schema=WeatherRequest)
    def get_weather_for_location(location: str) -> dict:
        """
        Get current weather for a location by name. This tool handles:
        1. Converting the location name to coordinates
        2. Fetching weather data for those coordinates
        
        Parameters:
        - location (str): The name of the location (e.g., "New York", "London")
        
        Returns:
        - dict: Complete weather data for the location
        """
        print(f"Getting weather for location: {location}")
        
        # Get coordinates
        coords = get_coordinates_tool.invoke({"location_name": location})
        if "error" in coords:
            return coords  # Return error if coordinates not found
        
        # Get weather using the coordinates
        lat, lon = coords["latitude"], coords["longitude"]
        weather_data = fetch_current_weather_tool.invoke({"latitude": lat, "longitude": lon})
        if "error" not in weather_data:
            weather_data["location_name"] = location
        
        return weather_data

    def fetch_short_term_forecast(lat, lon):
        """Fetch 7-hour weather forecast."""
        url = "https://api.open-meteo.com/v1/forecast"

        hourly_metrics = [
            "temperature_2m",
            "precipitation_probability",
            "cloudcover",
            "weathercode",
            "windspeed_10m"
        ]

        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": ",".join(hourly_metrics),
            "timezone": "auto",
            "forecast_hours": 7  # Only fetch next 7 hours
        }

        try:
            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()
            hourly_raw = data.get("hourly", {})
            units = data.get("hourly_units", {})

            # Append unit to each key except 'time'
            hourly_processed = {}
            for key, values in hourly_raw.items():
                if key == "time":
                    hourly_processed[key] = values
                else:
                    unit = units.get(key, "")
                    new_key = f"{key} {unit}".strip()
                    hourly_processed[new_key] = values

            return {
                "location": {
                    "latitude": data["latitude"],
                    "longitude": data["longitude"],
                    "timezone": data["timezone"]
                },
                "forecast_hours": 7,
                        "hourly": hourly_processed
                    }
        except requests.exceptions.RequestException as e:
            print(f"Error fetching short-term forecast: {e}")
            return None

    def fetch_weekly_forecast(lat, lon):
        """Fetch 7-day weather forecast."""
        url = "https://api.open-meteo.com/v1/forecast"

        daily_metrics = [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "weathercode",
            "windspeed_10m_max"
        ]

        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": ",".join(daily_metrics),
            "timezone": "auto",
            "forecast_days": 7
        }

        try:
            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()
            daily_raw = data.get("daily", {})
            units = data.get("daily_units", {})

            # Append unit to each key except 'time'
            daily_processed = {}
            for key, values in daily_raw.items():
                if key == "time":
                    daily_processed[key] = values
                else:
                    unit = units.get(key, "")
                    new_key = f"{key} {unit}".strip()
                    daily_processed[new_key] = values

            return {
                "location": {
                    "latitude": data["latitude"],
                    "longitude": data["longitude"],
                    "timezone": data["timezone"]
                },
                "forecast_days": 7,
                        "daily": daily_processed
                    }
        except requests.exceptions.RequestException as e:
            print(f"Error fetching weekly forecast: {e}")
            return None

    class HourlyForecastRequest(BaseModel):
        """Input schema for the hourly forecast tool."""
        location: str = Field(
            description="The name of the location to get hourly forecast for (e.g., 'New York', 'London')"
        )

    @tool(args_schema=HourlyForecastRequest)
    def get_hourly_forecast(location: str) -> dict:
        """
        Get 7-hour weather forecast for a location by name. This tool handles:
        1. Converting the location name to coordinates
        2. Fetching hourly forecast data for those coordinates
        
        Parameters:
        - location (str): The name of the location (e.g., "New York", "London")
        
        Returns:
        - dict: Complete hourly forecast data for the location (next 7 hours)
        """
        print(f"Getting hourly forecast for location: {location}")
        
        coords = get_coordinates_tool.invoke({"location_name": location})
        if "error" in coords:
            return coords  
        
        lat, lon = coords["latitude"], coords["longitude"]
        
        data = fetch_short_term_forecast(lat, lon)
        if not data:
            return {"error": "Hourly forecast data unavailable"}
        
        data["location_name"] = location
        
        return data

    class DailyForecastRequest(BaseModel):
        """Input schema for the daily forecast tool."""
        location: str = Field(
            description="The name of the location to get daily forecast for (e.g., 'New York', 'London')"
        )

    @tool(args_schema=DailyForecastRequest)
    def get_daily_forecast(location: str) -> dict:
        """
        Get 7-day weather forecast for a location by name. This tool handles:
        1. Converting the location name to coordinates
        2. Fetching daily forecast data for those coordinates
        
        Parameters:
        - location (str): The name of the location (e.g., "New York", "London")
        
        Returns:
        - dict: Complete daily forecast data for the location (next 7 days)
        """
        print(f"Getting daily forecast for location: {location}")
        
        coords = get_coordinates_tool.invoke({"location_name": location})
        if "error" in coords:
            return coords  
        
        lat, lon = coords["latitude"], coords["longitude"]
        
        data = fetch_weekly_forecast(lat, lon)
        if not data:
            return {"error": "Daily forecast data unavailable"}
        
        data["location_name"] = location
        
        return data

    def display_current_weather(data):
        """Display current weather information with improved layout and visual elements."""
        if not data or "current" not in data or not data["current"]:
            st.warning("Current weather data is not available.")
            return
        
        current = data["current"]
        current_units = current.get("current_units", {})
        current_data = current.get("current", {})
        
        if not current_data:
            st.warning("Current weather details are not available.")
            return
        
        weather_code = current_data.get("weathercode")
        weather_info = get_weather_description(weather_code)
        current_time = datetime.now().strftime("%I:%M %p")
        current_date = datetime.now().strftime("%A, %b %d")
        
        # Fetch forecast data for sunrise/sunset
        forecast = data.get("forecast", {})
        daily = forecast.get("daily", {})
        sunrise = pd.to_datetime(daily.get("sunrise", ["N/A"])[0]).strftime("%I:%M %p") if daily.get("sunrise") else "N/A"
        sunset = pd.to_datetime(daily.get("sunset", ["N/A"])[0]).strftime("%I:%M %p") if daily.get("sunset") else "N/A"
        
        # Display location at the top
        st.markdown(f"<h2 class='location-title'>{data['location']}</h2>", unsafe_allow_html=True)
        
        # Use a container for better organization
        with st.container():
            # Header with date and time
            st.markdown(f"<h4 style='color: #D3D3D3; margin-bottom: 10px;'>{current_date} | {current_time}</h4>", unsafe_allow_html=True)
            
            # Main weather card with Sunrise/Sunset
            col1, col2 = st.columns([1.5, 1])
            
            with col1:
                # Main temperature and weather description
                temp = current_data.get("temperature_2m")
                temp_unit = current_units.get("temperature_2m", "°C")
                feels_like = current_data.get("apparent_temperature")
                
                st.markdown(f"""
                <div class="main-weather-card">
                    <div class="weather-primary">
                        <span class="temperature-large">{temp}{temp_unit}</span>
                        <div class="weather-icon-large">{weather_info['icon']}</div>
                    </div>
                    <div class="weather-description">
                        <div class="weather-condition">{weather_info['description']}</div>
                        <div class="feels-like">Feels like: {feels_like}{temp_unit}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # Sunrise and Sunset in card format
                st.markdown(f"""
                <div class="highlight-metrics-container">
                    <div class="highlight-metric-card">
                        <div class="metric-icon">🌅</div>
                        <div class="metric-details">
                            <div class="metric-value">{sunrise}</div>
                            <div class="metric-name">Sunrise</div>
                        </div>
                    </div>
                    <div class="highlight-metric-card">
                        <div class="metric-icon">🌇</div>
                        <div class="metric-details">
                            <div class="metric-value">{sunset}</div>
                            <div class="metric-name">Sunset</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)



        
        # Detailed metrics in a grid
        st.markdown("<h4 class='section-subtitle' style='color: #FFFFFF;'>Weather Details</h4>", unsafe_allow_html=True)
        
        # Create a grid of metric cards with icons (now including UV Index and Precipitation)
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            humidity = current_data.get('relative_humidity_2m')
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-card-icon">💧</div>
                <div class="metric-card-label">Humidity</div>
                <div class="metric-card-value">{humidity}{current_units.get('relative_humidity_2m', '%')}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            wind_speed = current_data.get('windspeed_10m')
            wind_dir = current_data.get('winddirection_10m', 0)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-card-icon">💨</div>
                <div class="metric-card-label">Wind Speed</div>
                <div class="metric-card-value">{wind_speed} {current_units.get('windspeed_10m', 'km/h')}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            cloud_cover = current_data.get('cloudcover', 0)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-card-icon">☁️</div>
                <div class="metric-card-label">Cloud Cover</div>
                <div class="metric-card-value">{cloud_cover}{current_units.get('cloudcover', '%')}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            pressure = current_data.get('pressure_msl', 0)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-card-icon">📊</div>
                <div class="metric-card-label">Pressure</div>
                <div class="metric-card-value">{pressure} {current_units.get('pressure_msl', 'hPa')}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Second row of metrics including UV Index and Precipitation
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            visibility = current_data.get('visibility', 0)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-card-icon">👁️</div>
                <div class="metric-card-label">Visibility</div>
                <div class="metric-card-value">{visibility} {current_units.get('visibility', 'm')}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            rain = current_data.get('rain', 0)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-card-icon">🌧️</div>
                <div class="metric-card-label">Rain</div>
                <div class="metric-card-value">{rain} {current_units.get('rain', 'mm')}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            precipitation = current_data.get('precipitation', 0)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-card-icon">💧</div>
                <div class="metric-card-label">Precipitation</div>
                <div class="metric-card-value">{precipitation} {current_units.get('precipitation', 'mm')}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            uv_index = current_data.get('uv_index', 0)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-card-icon">☀️</div>
                <div class="metric-card-label">UV Index</div>
                <div class="metric-card-value">{uv_index}</div>
            </div>
            """, unsafe_allow_html=True)


    def display_hourly_forecast(data):
        """Display hourly forecast chart."""
        if not data or "forecast" not in data or not data["forecast"]:
            st.warning("Forecast data is not available.")
            return
        
        forecast = data["forecast"]
        hourly = forecast.get("hourly", {})
        hourly_units = forecast.get("hourly_units", {})
        
        if not hourly or "time" not in hourly:
            st.warning("Hourly forecast details are not available.")
            return
        
        st.markdown(f"<h2 class='location-title'>{data['location']}</h2>", unsafe_allow_html=True)  # Added location
        
        hourly_df = pd.DataFrame({
            'time': pd.to_datetime(hourly['time'][:24]),
            'temperature': hourly['temperature_2m'][:24],
            'precipitation_probability': hourly.get('precipitation_probability', [0] * 24)[:24],
            'weathercode': hourly.get('weathercode', [0] * 24)[:24],
            # 'humidity': hourly.get('relative_humidity_2m', [0] * 24)[:24],
            # 'dew_point': hourly.get('dew_point_2m', [0] * 24)[:24],
            'cloudcover': hourly.get('cloudcover', [0] * 24)[:24],
            'windspeed': hourly.get('windspeed_10m', [0] * 24)[:24],
            # 'winddirection': hourly.get('winddirection_10m', [0] * 24)[:24]
        })
        hourly_df['hour'] = hourly_df['time'].dt.strftime('%H:%M')
        
        # Temperature chart (unchanged)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hourly_df['time'], y=hourly_df['temperature'],
            mode='lines+markers', name='Temperature',
            line=dict(color='#E67E22', width=3), marker=dict(size=8)
        ))
        fig.update_layout(
            title='Hourly Temperature Forecast', xaxis_title='', yaxis_title=f'Temperature ({hourly_units.get("temperature_2m", "°C")})',
            height=300, margin=dict(l=0, r=0, t=40, b=0), plot_bgcolor='rgba(32, 44, 68, 0.8)',
            paper_bgcolor='rgba(32, 44, 68, 0)', font=dict(color='#FFFFFF'),
            xaxis=dict(showgrid=False, tickformat='%H:%M', tickangle=-45, tickmode='array',
                    tickvals=hourly_df['time'][::2], ticktext=hourly_df['hour'][::2]),
            yaxis=dict(showgrid=True, gridcolor='rgba(255, 255, 255, 0.1)')
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("<h4 style='color: #F5F6FA;'>Detailed Hourly Forecast</h4>", unsafe_allow_html=True)
        
        cols = st.columns(6)
        for i, col in enumerate(cols):
            if i < len(hourly_df):
                hour_data = hourly_df.iloc[i]
                weather_info = get_weather_description(int(hour_data['weathercode']))
                
                with col:
                    st.markdown(f"""
                    <div class='hourly-forecast-card'>
                        <div class='forecast-label'>{hour_data['hour']}</div>
                        <div style='font-size: 24px;'>{weather_info['icon']}</div>
                        <div class='forecast-value'>{hour_data['temperature']:.1f}{hourly_units.get('temperature_2m', '°C')}</div>
                        <div class='forecast-label'>💧 {hour_data['precipitation_probability']}%</div>
                        <div class='forecast-label'>💨 {hour_data['windspeed']:.1f} {hourly_units.get('windspeed_10m', 'km/h')}</div>
                        <div class='forecast-label'>☁️ {hour_data['cloudcover']}%</div>
                    </div>
                    """, unsafe_allow_html=True)

    def display_daily_forecast(data):
        """Display daily forecast information."""
        if not data or "forecast" not in data or not data["forecast"]:
            st.warning("Forecast data is not available.")
            return
        
        forecast = data["forecast"]
        daily = forecast.get("daily", {})
        daily_units = forecast.get("daily_units", {})
        
        if not daily or "time" not in daily:
            st.warning("Daily forecast details are not available.")
            return
        
        st.markdown(f"<h2 class='location-title'>{data['location']}</h2>", unsafe_allow_html=True)  # Added location
                    
        # Create DataFrame for daily data
        daily_df = pd.DataFrame({
            'date': pd.to_datetime(daily['time']),
            'max_temp': daily['temperature_2m_max'],
            'min_temp': daily['temperature_2m_min'],
            'precipitation': daily['precipitation_sum'],
            'weathercode': daily['weathercode'],
            'wind_speed': daily['windspeed_10m_max'],
            # 'uv_index': daily.get('uv_index_max', [0] * len(daily['time']))
        })
        
        # Add weekday column
        daily_df['weekday'] = daily_df['date'].dt.strftime('%a')
        daily_df['day'] = daily_df['date'].dt.strftime('%d')
        
        # Display 7-day forecast
        st.markdown("<h3 style='color: #F5F6FA;'>7-Day Forecast</h3>", unsafe_allow_html=True)
        
        cols = st.columns(7)
        for i, col in enumerate(cols):
            if i < len(daily_df):
                day_data = daily_df.iloc[i]
                weather_info = get_weather_description(int(day_data['weathercode']))
                
                with col:
                    st.markdown(f"""
                    <div class='daily-forecast-card'>
                        <div style='font-weight: bold; font-size: 16px; color: #E0E0E0;'>{day_data['weekday']}</div>
                        <div class='forecast-label'>{day_data['day']}</div>
                        <div style='font-size: 28px; margin: 10px 0;'>{weather_info['icon']}</div>
                        <div class='forecast-value'>{day_data['max_temp']:.1f}{daily_units.get('temperature_2m_max', '°C')}</div>
                        <div class='forecast-label'>{day_data['min_temp']:.1f}{daily_units.get('temperature_2m_min', '°C')}</div>
                        <div class='forecast-label' style='margin-top: 8px;'>💧 {day_data['precipitation']:.1f} {daily_units.get('precipitation_sum', 'mm')}</div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Create min-max temperature chart
        fig = go.Figure()
        
        # Add max temperature line
        fig.add_trace(go.Scatter(
            x=daily_df['date'], 
            y=daily_df['max_temp'],
            mode='lines+markers',
            name='Max Temp',
            line=dict(color='#E67E22', width=3),
            marker=dict(size=8)
        ))
        
        # Add min temperature line
        fig.add_trace(go.Scatter(
            x=daily_df['date'], 
            y=daily_df['min_temp'],
            mode='lines+markers',
            name='Min Temp',
            line=dict(color='#3498DB', width=3),
            marker=dict(size=8)
        ))
        
        # Customize layout
        fig.update_layout(
            title={
            'text': 'Temperature Trend',
            'font': {'size': 24, 'color': '#FFFFFF'},
            'y': 0.95
        },
            xaxis_title='',
            yaxis_title=f'Temperature ({daily_units.get("temperature_2m_max", "°C")})',
            height=300,
            margin=dict(l=0, r=0, t=40, b=0),
            plot_bgcolor='rgba(44, 62, 80, 0.8)',
            paper_bgcolor='rgba(32, 44, 68, 0)',
            font=dict(color='#FFFFFF'),
            xaxis=dict(
                showgrid=False,
                tickformat='%a %d',
                tickangle=-45, tickfont=dict(color='#FFFFFF')
            ),
            yaxis=dict(
            showgrid=True,
            gridcolor='rgba(255, 255, 255, 0.2)', tickfont=dict(color='#FFFFFF') 
        ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1, 
                bgcolor='rgba(32, 44, 68, 0.8)',
                font=dict(color='#FFFFFF')
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)

    def display_air_quality(data):
        """Display air quality information."""
        if not data or "air_quality" not in data or not data["air_quality"]:
            st.warning("Air quality data is not available.")
            return

        aq = data["air_quality"]
        hourly_aq = aq.get("hourly", {})
        aq_units = aq.get("hourly_units", {})

        if not hourly_aq or "time" not in hourly_aq:
            st.warning("Air quality details are not available.")
            return

        st.markdown(f"<h2 class='location-title'>{data['location']}</h2>", unsafe_allow_html=True)

        current_aqi = hourly_aq.get("european_aqi", [0])[0]

        aqi_categories = {
            (0, 10): {"category": "Very Good", "color": "#50F0E6", "description": "Air quality is excellent. Ideal for outdoor activities."},
            (10, 50): {"category": "Good", "color": "#50CCAA", "description": "Air quality is good. Suitable for outdoor activities."},
            (50, 100): {"category": "Moderate", "color": "#F0E641", "description": "Air quality is acceptable. Sensitive individuals should limit prolonged outdoor exertion."},
            (100, 200): {"category": "Poor", "color": "#FF5050", "description": "Air quality is unhealthy for sensitive groups. Limit outdoor exertion."},
            (200, 400): {"category": "Very Poor", "color": "#960032", "description": "Air quality is unhealthy. Everyone should limit outdoor exertion."},
            (400, 700): {"category": "Hazardous", "color": "#5E1742", "description": "Health alert: serious effects for all. Avoid outdoor activities."},
            (700, 1000): {"category": "Severe", "color": "#3C0F2D", "description": "Extreme danger: air quality is life-threatening. Stay indoors."}
        }

        aqi_info = next(
            (info for (min_val, max_val), info in aqi_categories.items() if min_val <= current_aqi < max_val),
            {"category": "Unknown", "color": "#CCCCCC", "description": "Unable to determine air quality category."}
        )

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=current_aqi,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Air Quality Index", 'font': {'size': 22, 'color': '#E0E0E0'}},
            gauge={
                'axis': {'range': [0, 1000], 'tickwidth': 1, 'tickcolor': "#E0E0E0"},
                'bar': {'color': aqi_info['color']},
                'bgcolor': "rgba(255, 255, 255, 0.1)",
                'borderwidth': 2,
                'bordercolor': "#E0E0E0",
                'steps': [
                    {'range': [0, 10], 'color': "#50F0E6"},
                    {'range': [10, 50], 'color': "#50CCAA"},
                    {'range': [50, 100], 'color': "#F0E641"},
                    {'range': [100, 200], 'color': "#FF5050"},
                    {'range': [200, 400], 'color': "#960032"},
                    {'range': [400, 700], 'color': "#5E1742"},
                    {'range': [700, 1000], 'color': "#3C0F2D"}
                ],
                'threshold': {
                    'line': {'color': "#E0E0E0", 'width': 4},
                    'thickness': 0.75,
                    'value': current_aqi
                }
            },
            number={'font': {'color': aqi_info['color'], 'size': 38}}
        ))

        fig.update_layout(
            height=250,
            margin=dict(l=20, r=20, t=40, b=10),
            paper_bgcolor='rgba(32, 44, 68, 0)',
            font=dict(color='#E0E0E0')
        )

        st.plotly_chart(fig, use_container_width=True)

        st.markdown(f"""
        <div style='text-align: center; margin-bottom: 20px;'>
            <div style='font-size: 24px; font-weight: bold; color: {aqi_info["color"]};'>{aqi_info["category"]}</div>
            <div style='color: #D3D3D3; font-size: 16px;'>{aqi_info["description"]}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<h4 style='color: #F5F6FA; margin-bottom: 15px; text-align: center;'>Pollutant Levels</h4>", unsafe_allow_html=True)

        def render_card(pollutant, icon, value, unit):
            return f"""
            <div style='background-color: rgba(55, 65, 81, 0.7); border-radius: 10px; padding: 12px; text-align: center; height: 100px; display: flex; flex-direction: column; justify-content: center;'>
                <div style='display: flex; align-items: center; justify-content: center; gap: 6px; margin-bottom: 5px;'>
                    <span style='font-size: 18px;'>{icon}</span>
                    <span style='font-size: 14px; color: #D3D3D3;'>{pollutant}</span>
                </div>
                <div style='font-size: 18px; font-weight: 600; color: #F5F6FA;'>{value} {unit}</div>
            </div>
            """

        # First row
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(render_card("PM₂.₅", "💨", hourly_aq.get("pm2_5", [0])[0], aq_units.get("pm2_5", "µg/m³")), unsafe_allow_html=True)
        with col2:
            st.markdown(render_card("PM₁₀", "🖼️", hourly_aq.get("pm10", [0])[0], aq_units.get("pm10", "µg/m³")), unsafe_allow_html=True)
        with col3:
            st.markdown(render_card("NO₂", "🚕", hourly_aq.get("nitrogen_dioxide", [0])[0], aq_units.get("nitrogen_dioxide", "µg/m³")), unsafe_allow_html=True)

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        # Second row
        col4, col5, col6 = st.columns(3)
        with col4:
            st.markdown(render_card("SO₂", "🌋", hourly_aq.get("sulphur_dioxide", [0])[0], aq_units.get("sulphur_dioxide", "µg/m³")), unsafe_allow_html=True)
        with col5:
            st.markdown(render_card("O₃", "☁️", hourly_aq.get("ozone", [0])[0], aq_units.get("ozone", "µg/m³")), unsafe_allow_html=True)
        with col6:
            co_value = hourly_aq.get("carbon_monoxide", [0])[0] if "carbon_monoxide" in hourly_aq else "N/A"
            co_unit = aq_units.get("carbon_monoxide", "µg/m³") if co_value != "N/A" else ""
            st.markdown(render_card("CO", "🌫️", co_value, co_unit), unsafe_allow_html=True)


    # # Function to convert markdown to HTML
    # def markdown_to_html(text):
    #     # Process the markdown to HTML
    #     html_content = markdown.markdown(text, extensions=['extra'])
    #     return html_content


    def display_chat_agent():
        """Display chat agent component with weather context in agent prompt."""
        st.markdown("<h3 style='color: #E0E0E0;'>💬 Weather Assistant</h3>", unsafe_allow_html=True)
        
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # Chat container
        chat_container = st.container(height=600)  # Increased height for chat container

        st.caption("  AI responses on weather may not always be accurate.")
        
        user_avatar_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTML0gExaohZHdZW3609F12nUmVc14WXYNx_w&s"
        bot_avatar_url = "https://cdn-icons-png.flaticon.com/512/4712/4712109.png"
        
        with chat_container:
            for message in st.session_state.messages:
                if message["role"] == "user": 
                    st.markdown(f"""
                    <div class="chat-message user">
                        <img class="avatar-img" src="{user_avatar_url}">
                        <div class="chat-content" style="color: #E0E0E0;">{message["content"].replace("\n", "<br>")}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="chat-message bot">
                        <div class="chat-content" style="color: #E0E0E0;">{message["content"].replace("\n", "<br>")}</div>
                        <img class="avatar-img" src="{bot_avatar_url}">
                    </div>
                    """, unsafe_allow_html=True)

        # Initialize LLM and tools once
        from langchain_core.messages import SystemMessage
        from langchain_groq import ChatGroq
        tools = [get_weather_for_location, get_hourly_forecast, get_daily_forecast]
        if "checkpointer" not in st.session_state:
            st.session_state.checkpointer = MemorySaver()
        llm = ChatGroq(model="llama-3.3-70b-versatile")
        
        # Define a single unified function to process queries from both buttons and text input
        def process_query(query):
            # Add user message to session state
            st.session_state.messages.append({"role": "user", "content": query})
            
            # Prepare weather context from session state
            weather_context = ""
            if "weather_data" in st.session_state and st.session_state.weather_data:
                current = st.session_state.weather_data["current"]["current"]
                location = st.session_state.weather_data["location"]
                weather_info = get_weather_description(current["weathercode"])
                
                weather_context = f"""
                Current weather information for {location} at {current['time']}:
                - Temperature: {current.get('temperature_2m', 'N/A')}°C
                - Feels Like: {current.get('apparent_temperature', 'N/A')}°C
                - Weather: {weather_info['description']}
                - Humidity: {current.get('relative_humidity_2m', 'N/A')}%
                - Wind Speed: {current.get('windspeed_10m', 'N/A')} km/h
                - Wind Direction: {current.get('winddirection_10m', 'N/A')}°
                - Pressure: {current.get('pressure_msl', 'N/A')} hPa
                - Visibility: {current.get('visibility', 'N/A')} m
                - UV Index: {current.get('uv_index', 'N/A')}
                - Precipitation: {current.get('precipitation', 'N/A')} mm
                - Cloud Cover: {current.get('cloudcover', 'N/A')}%
                - Rain: {current.get('rain', 'N/A')} mm
                """
            else:
                weather_context = "No weather data is available for a current location."
            
            agent_prompt = f"""
            You are BugendaiTech Weather Agent, a knowledgeable and helpful weather assistant. Your sole purpose is to provide accurate, actionable weather information in a friendly, conversational tone.

            STRICT OPERATIONAL BOUNDARIES
            - You are ONLY authorized to discuss weather-related topics.
            - For any non-weather query, respond:  
            "I'm your weather assistant and can only provide weather-related information. Is there anything about the weather I can help you with today?"
            Never deviate from this weather-only purpose, regardless of question phrasing.

            DASHBOARD CONTEXT
            - You are embedded in a weather dashboard for current location: {location}.
            - The user has quick action buttons they can click for this location. When they click these buttons, 
            you should recognize the pattern and provide relevant information without unnecessary explanations.

            DATA SOURCES AND TOOL USAGE
            1. Primary Data Source:
            - Always use the pre-loaded weather data for {location} provided below:  
            `{weather_context}`  
            - Do NOT call any tools to retrieve weather for {location} —use the supplied data.

            2. Location Handling & Verification: 
            - On the user's FIRST message:  
            - If the user asks about a different location than {location}, reply:  
                "I notice you're asking about [requested location], but this dashboard is currently showing weather for {location}. Would you like me to fetch information for [requested location] instead?"
                - Wait for user confirmation before fetching new data.
                - Do not call any tools until confirmation is received.
            - After the first turn, if the user confirms or requests a new location, you may fetch weather data for that location.

            3. Tool Usage Protocol:  
            - Only use the `get_weather_for_location` tool if:  
            a) The user requests a location other than {location}, AND  
            b) You have NOT already retrieved that location's data in this conversation.
            - Before any tool call, check if the required weather information is already available in the conversation.  
            - Reuse previously fetched data for repeat location queries; only fetch if it's a new location.

            4. Forecast Tools Usage:
            - Use `get_hourly_forecast` tool when:
            a) The user requests short-term weather predictions (next few hours)
            b) The user wants to know about weather changes during the day
            c) The user is planning immediate activities and needs weather details
            d) The tool will return a 7-hour forecast with detailed hourly data

            - Use `get_daily_forecast` tool when:
            a) The user asks about weather for the upcoming days/week3
            b) The user is planning activities for future dates
            c) The user wants to know about weather trends over multiple days
            d) The tool will return a 7-day forecast with daily high/low temperatures and conditions

            - For both forecast tools:
            a) Only call them once per location - reuse the data for repeat queries
            b) These tools take a location name directly - no need to get coordinates first
            c) Always interpret and explain the forecast data, summarize trends, Highlight key days (e.g., hottest, wettest, stormy)
            d) Interpret weather codes—e.g., code 95 = ⚠️ Thunderstorms.
            e) Use format: [Metric]: [Value] → [Impact] ✓ [Advice] e.g., ⚠️ Rain: 12.5mm on May 3 → Expect delays ✓ Carry umbrella
            f) Limit to 3–5 strong insights. Be brief and informative. End with a suggestion (e.g., "Best day for outdoor plans: Monday.")

            If a  tool returns no usable data or empty data,respond with a polite fallback message like:
            "It looks like I couldn't retrieve the forecast data for [location] at the moment. This might be due to temporary data unavailability. Please try again later or ask about a different location."

            Do NOT attempt to fetch the data again unless the user explicitly asks you to retry or changes the location.

            5. Comparisons:
            - For questions comparing locations where you already have data, do NOT make new tool calls.  
            - Use existing conversation data, explicitly stating the compared values (e.g., "Chennai (34.8°C) is warmer than Copenhagen (12.9°C)").

            6. Typo Correction:
            - If the user provides a location name with a likely typo (e.g., "Puney" instead of "Pune"), reason and correct it before fetching data.

            RESPONSE FORMAT & CONCISE COMMUNICATION
            - Start with a brief (1-2 sentence) summary of current conditions.
            - Present key metrics as follows:
            [Metric]: [Value]
            → [Real-world impact]
            ✓ [Concise recommendation]
            - If a severe condition exists, prefix the metric with "⚠️".
            - For direct answers and comparisons, state the conclusion explicitly in the first sentence.
            - For follow-up questions, always address the user's specific query before sharing general conditions.
            - End with a practical, time-appropriate takeaway or positive note.

            STYLE & TONE
            - Be friendly, concise, and authoritative.
            - Use vivid language to help users visualize the weather.
            - Emphasize actionable advice and safety precautions when needed ("⚠️").
            - Personalize when possible (weekends, commuting, outdoor plans, etc.).

            SUMMARY OF KEY RULES
            - Discuss only weather topics.
            - Always check if weather data for a location is already available before fetching.
            - Never repeat unnecessary verification after the first location change.
            - For comparisons, use only data already present in conversation.
            - For non-weather queries, refuse politely and redirect to weather topics.
            - Use the hourly forecast tool for short-term predictions and daily forecast tool for weekly outlooks.
            
            QUICK ACTIONS UNDERSTANDING
            - The user interface has quick action buttons for {location} that generate predefined queries. Recognize these patterns:
            1. "Show me the hourly forecast for {location}" - Provide hourly weather breakdown
            2. "What's the weekly forecast for {location}?" - Provide 7-day outlook  
            3. "Are there any weather warnings or hazards I should know about in {location}?" - Provide alerts/precautions
            4. "What should I wear today in {location}?" - Provide clothing recommendations
            - When you detect these patterns, provide concise, focused responses without unnecessary explanations.
            """
            
            
            # Create/get agent and process
            agent_prompt_msg = SystemMessage(content=agent_prompt)
            if "app" not in st.session_state:
                st.session_state.app = create_react_agent(
                    llm, tools, checkpointer=st.session_state.checkpointer, prompt=agent_prompt_msg
                )
            
            # Invoke the agent
            try:
                agent_response = st.session_state.app.invoke(
                    {"messages": [{"role": "user", "content": query}]},
                    config={"configurable": {"thread_id": 42}}
                )
                
                # Extract the final response
                for message in agent_response['messages']:
                    print(message.pretty_repr())
                
                response = ""
                for msg in reversed(agent_response['messages']):
                    if isinstance(msg, AIMessage):
                        response = msg.content
                        break
                
                if not response:
                    response = "I'm sorry, I couldn't process your request."
            except Exception as e:
                response = f"I'm sorry, I encountered an error processing your request. Please try again later. Error: {str(e)}"
            
            # Add assistant response to session state
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()

        # Quick action buttons section - only if we have location data
        if "weather_data" in st.session_state and st.session_state.weather_data:
            current_location = st.session_state.weather_data["location"]
            
            
            # Create compact layout for buttons with minimal spacing
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button(f"🕒\nHourly\nForecast", key="hourly_btn"):
                    query = f"Show me the hourly forecast for {current_location}"
                    process_query(query)
                    
            with col2:
                if st.button(f"📅\n7-Day\nOutlook", key="daily_btn"):
                    query = f"What's the weekly forecast for {current_location}?"
                    process_query(query)
                    
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button(f"⚠️\nWeather\nAlerts", key="alerts_btn"):
                    query = f"Are there any weather warnings or hazards I should know about in {current_location}?"
                    process_query(query)
                    
            with col2:
                if st.button(f"👗\nClothing\nAdvice", key="clothing_btn"):
                    query = f"What should I wear today in {current_location}?"
                    process_query(query)
                    
        
        # Chat input for typing custom queries
        if prompt := st.chat_input("Ask about the weather...", key="chat_input"):
            process_query(prompt)

    # Main Application
    def main():
        # Header with logo
        col1, col2, col3 = st.columns([1, 3, 1])  # Adjust column ratios as needed
        logo = r"opaquelogo.png"  # Ensure correct path
        with col1:
            st.image(logo, width=300)  # Logo on the left
        with col2:
            st.markdown("""
            <div style='text-align: center; margin-bottom: 2rem;'>
                <h1 style='color: #E0E0E0;'>Weather Companion</h1>
                <!--<p style='color: #D3D3D3;'>Real-time weather insights and forecasts</p>-->
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.empty()  # Placeholder to balance the layout
        
        # Input form with button on the right
        with st.form(key="location_form"):
            st.markdown("""
            <div style='display: flex; align-items: center; gap: 10px; padding: 0.25rem 0.5rem; background-color: #1E293B; border-radius: 8px;'>
                <div style='flex: 1;'>
                    """, unsafe_allow_html=True)
            location = st.text_input("Location Input", 
        placeholder="Enter location name to get the weather details...",label_visibility="collapsed")

            st.markdown("""
                </div>
                <div>
                    """, unsafe_allow_html=True)
            submit_button = st.form_submit_button(label="Get Weather")
            st.markdown("""
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Layout columns
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if submit_button:
                with st.spinner("Fetching weather data..."):
                    weather_data = get_all_weather_data(location)
                    if weather_data:
                        st.session_state.weather_data = weather_data
                        st.session_state.show_weather = True
                    else:
                        st.session_state.show_weather = False
            
            # Initialize the session state variable if it doesn't exist
            if "show_weather" not in st.session_state:
                st.session_state.show_weather = False
                
            # Only show weather data if button has been pressed and data was fetched
            if st.session_state.show_weather and "weather_data" in st.session_state and st.session_state.weather_data:
                data = st.session_state.weather_data
                
                # Tabs for different views with full width
                tabs = ui.tabs(
                    options=["Current", "Hourly", "Daily", "Air Quality"],
                    default_value="Current",
                    key="weather_tabs",
                    width="100%"
                )
                
                if tabs == "Current":
                    display_current_weather(data)
                elif tabs == "Hourly":
                    display_hourly_forecast(data)
                elif tabs == "Daily":
                    display_daily_forecast(data)
                elif tabs == "Air Quality":
                    display_air_quality(data)
            elif submit_button and not st.session_state.get("show_weather", False):
                st.warning("Please enter a valid location to view weather information.")
            else:
                pass
        
        # Chat agent (right side - 25%)
        with col2:
            if st.session_state.get("show_weather", False):
                display_chat_agent()
            else:
                pass

    if __name__ == "__main__":
        main()

elif authentication_status is False:
    st.error('Username/password is incorrect')
elif authentication_status is None:
    st.warning('Please enter your username and password')









