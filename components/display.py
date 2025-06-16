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
from components.dashboard import get_weather_description, fetch_current_weather, fetch_forecast_weather, fetch_air_quality,get_all_weather_data, get_weather_description

from pydantic import BaseModel, Field
import streamlit.components.v1 as components

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
                            <div style='font-weight: bold; font-size: 16px; color: #E0E0E0;'>{hour_data['hour']}</div>
                            <div style='font-size: 24px; margin: 10px 0;'>{weather_info['icon']}</div>
                            <div class='forecast-value' style='color: #ff8c42;'>{hour_data['temperature']:.1f}{hourly_units.get('temperature_2m', '°C')}</div>
                            <div class='forecast-label' style='color: #E0E0E0;'>💧 {hour_data['precipitation_probability']}%</div>
                            <div class='forecast-label' style='color: #E0E0E0;'>💨 {hour_data['windspeed']:.1f} {hourly_units.get('windspeed_10m', 'km/h')}</div>
                            <div class='forecast-label' style='color: #E0E0E0;'>☁️ {hour_data['cloudcover']}%</div>
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
                            <div class='forecast-label' style='color: #D3D3D3;'>{day_data['day']}</div>
                            <div style='font-size: 28px; margin: 10px 0;'>{weather_info['icon']}</div>
                            <div class='forecast-value' style='color: #ff8c42;'>{day_data['max_temp']:.1f}{daily_units.get('temperature_2m_max', '°C')}</div>
                            <div class='forecast-label' style='color: #E0E0E0;'>{day_data['min_temp']:.1f}{daily_units.get('temperature_2m_min', '°C')}</div>
                            <div class='forecast-label' style='margin-top: 8px; color: #E0E0E0;'>💧 {day_data['precipitation']:.1f} {daily_units.get('precipitation_sum', 'mm')}</div>
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
            <div style='background-color: #2d4b73; border-radius: 10px; padding: 12px; text-align: center; height: 100px; display: flex; flex-direction: column; justify-content: center; border: 1px solid rgba(255, 140, 66, 0.1); transition: transform 0.2s;'>
                <div style='display: flex; align-items: center; justify-content: center; gap: 6px; margin-bottom: 5px;'>
                    <span style='font-size: 18px;'>{icon}</span>
                    <span style='font-size: 14px; color: #E0E0E0;'>{pollutant}</span>
                </div>
                <div style='font-size: 18px; font-weight: 600; color: #ff8c42;'>{value} {unit}</div>
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
