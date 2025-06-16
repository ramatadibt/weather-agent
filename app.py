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

from styles.css import load_css 
from components.dashboard import get_weather_description, fetch_current_weather, fetch_forecast_weather, fetch_air_quality,get_all_weather_data, get_weather_description
from components.display import display_current_weather, display_hourly_forecast, display_daily_forecast, display_air_quality


# LangChain and LangGraph Imports
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.messages import SystemMessage
from langchain_core.tools import BaseTool, tool
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
import streamlit.components.v1 as components

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


config_yaml = st.secrets["config"]
config = yaml.safe_load(config_yaml)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    auto_hash=False  # Important since you've pre-hashed the passwords
)

name, authentication_status, username = authenticator.login('main')

if authentication_status:
    zoom_script = """
<script>
  // Function to detect browser
  function detectBrowser() {
    const userAgent = navigator.userAgent;
    
    if (userAgent.indexOf("Edg") !== -1) {
      return "Edge";
    } else if (userAgent.indexOf("Chrome") !== -1) {
      return "Chrome";
    } else if (userAgent.indexOf("Firefox") !== -1) {
      return "Firefox";
    } else if (userAgent.indexOf("Safari") !== -1) {
      return "Safari";
    } else {
      return "Unknown";
    }
  }

  // Function to set zoom level
  function setZoomLevel(zoomLevel) {
    // Chrome, Safari, Edge
    document.body.style.zoom = zoomLevel + "%";
    
    // Firefox
    if (navigator.userAgent.indexOf('Firefox') !== -1) {
      document.body.style.transform = `scale(${zoomLevel/100})`;
      document.body.style.transformOrigin = "0 0";
    }
    
    // For IE
    if (document.body.style.zoom === undefined && document.body.style.MozTransform === undefined) {
      // Try CSS zoom
      var style = document.createElement('style');
      style.type = 'text/css';
      style.innerHTML = 'body {zoom: ' + zoomLevel + '%;}';
      document.getElementsByTagName('head')[0].appendChild(style);
    }
  }
  
  // Set zoom when page loads based on browser
  document.addEventListener('DOMContentLoaded', function() {
    const browser = detectBrowser();
    
    if (browser === "Chrome") {
      setZoomLevel(75);
    } else if (browser === "Edge") {
      setZoomLevel(80);
    } else {
      // Default for other browsers
      setZoomLevel(75);
    }
    
    console.log("Browser detected:", browser, "- Zoom level set accordingly");
  });
</script>
"""
    components.html(zoom_script, height=0)

    # Apply custom CSS
    st.markdown(load_css(), unsafe_allow_html=True)


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
        # llm = ChatGroq(model = "meta-llama/llama-4-scout-17b-16e-instruct")
        
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
            - For any non weather related query, respond:  
            "I'm your weather assistant and can only provide weather-related information. Is there anything about the weather I can help you with today?"
            Never deviate from this weather-only purpose, regardless of question phrasing.
            - Do not respond to cheeky, inappropriate, or suggestive requests that use weather as a pretext for personal relationship advice. 
            - When detecting a personal scenario (like 'Can I go outside with my GF'), ignore the personal context entirely and respond only with relevant weather data if a location is specified

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
            col1, col2 = st.columns([1, 1], gap="small")
            
            with col1:
                if st.button(f"🕒 \nHourly\nForecast", key="hourly_btn",use_container_width=True):
                    query = f"Show me the hourly forecast for {current_location}"
                    process_query(query)
                    
            with col2:
                if st.button(f"📅 \n7-Day  \nOutlook", key="daily_btn",use_container_width=True):
                    query = f"What's the weekly forecast for {current_location}?"
                    process_query(query)
                    
            col1, col2 = st.columns([1, 1], gap="small")
            
            with col1:
                if st.button(f"⚠️\nWeather  \nAlerts", key="alerts_btn",use_container_width=True):
                    query = f"Are there any weather warnings or hazards I should know about in {current_location}?"
                    process_query(query)
                    
            with col2:
                if st.button(f"👗\nClothing\nAdvice", key="clothing_btn",use_container_width=True):
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









