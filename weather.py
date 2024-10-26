import requests
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import create_engine, Column, Float, Integer, Date, String, func
from sqlalchemy.orm import declarative_base, sessionmaker
from PIL import Image
from io import BytesIO
import requests.exceptions
from collections import defaultdict
from smtplib import SMTP  # For email alerts (optional)
import os

# ----------------------------
# Database Setup
# ----------------------------
Base = declarative_base()
engine = create_engine('sqlite:///weather_data.db')
Session = sessionmaker(bind=engine)
session = Session()

# Define Database Models
class CurrentWeather(Base):
    __tablename__ = 'current_weather'
    id = Column(Integer, primary_key=True)
    city = Column(String)
    main_condition = Column(String)
    temperature = Column(Float)
    feels_like = Column(Float)
    timestamp = Column(Date)

class DailySummary(Base):
    __tablename__ = 'daily_summary'
    id = Column(Integer, primary_key=True)
    city = Column(String)
    date = Column(Date)
    avg_temp = Column(Float)
    max_temp = Column(Float)
    min_temp = Column(Float)
    dominant_condition = Column(String)

Base.metadata.create_all(engine)

# ----------------------------
# Configuration and Globals
# ----------------------------
# Set your API key securely using an environment variable
API_KEY = os.getenv('WEATHER_API_KEY', '2fb50e3750a0e14469f3dd2184e31e54')  # Replace with your actual API key
CITIES = ["Delhi", "Mumbai", "Chennai", "Bangalore", "Kolkata", "Hyderabad"]  # Predefined cities

API_URL = "http://api.openweathermap.org/geo/1.0/direct"
WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_API_URL = "https://api.openweathermap.org/data/2.5/forecast"

# Alert Thresholds and Tracking
ALERT_THRESHOLD = 35  # Default threshold for temperature
TEMP_ALERT_CONSECUTIVE_COUNT = 2  # Alert after 2 consecutive breaches
consecutive_breach_count = defaultdict(int)  # Tracks breaches per city

# Scheduler Initialization
scheduler = BackgroundScheduler()

# ----------------------------
# Helper Functions
# ----------------------------

def fetch_coordinates(city_name):
    """Fetch latitude and longitude for a given city."""
    try:
        response = requests.get(API_URL, params={'q': city_name, 'limit': 1, 'appid': API_KEY})
        response.raise_for_status()
    except requests.ConnectionError:
        st.error("No internet connection. Please check your connection and try again.")
        return None
    except requests.RequestException as e:
        st.error(f"Error fetching coordinates for {city_name}: {e}")
        return None

    data = response.json()
    if data:
        return {
            'lat': data[0]['lat'],
            'lon': data[0]['lon'],
            'id': data[0].get('id')  # Use .get() to avoid KeyError
        }
    return None

def fetch_weather_data(lat, lon, units='metric'):
    """Fetch current weather data for given coordinates."""
    try:
        response = requests.get(WEATHER_API_URL, params={'lat': lat, 'lon': lon, 'appid': API_KEY, 'units': units})
        response.raise_for_status()
    except requests.ConnectionError:
        st.error("No internet connection. Please check your connection and try again.")
        return None
    except requests.RequestException as e:
        st.error(f"Error fetching weather data: {e}")
        return None

    data = response.json()
    return {
        'city': data['name'],
        'main': data['weather'][0]['main'],
        'temp': data['main']['temp'],  # Already in Celsius if units='metric'
        'feels_like': data['main']['feels_like'],
        'icon': data['weather'][0]['icon'],  # Get the weather icon
        'timestamp': datetime.now()
    }

def fetch_weather_forecast(lat, lon, units='metric'):
    """Fetch 5-day weather forecast for given coordinates."""
    try:
        response = requests.get(FORECAST_API_URL, params={'lat': lat, 'lon': lon, 'appid': API_KEY, 'units': units})
        response.raise_for_status()
    except requests.ConnectionError:
        st.error("No internet connection. Please check your connection and try again.")
        return None
    except requests.RequestException as e:
        st.error(f"Error fetching weather forecast: {e}")
        return None

    data = response.json()
    print(data)
    forecast_list = []
    if 'list' in data:
        for forecast in data['list']:
            if 'main' in forecast and 'weather' in forecast:
                forecast_list.append({
                    'date': forecast['dt_txt'],
                    'main': forecast['weather'][0]['main'],
                    'temp': forecast['main'].get('temp', None),  # Use get() to avoid KeyError
                    'feels_like': forecast['main'].get('feels_like', None),
                    'icon': forecast['weather'][0].get('icon', None),
                })

    return forecast_list

def store_current_weather(weather_data):
    """Store current weather data in the database."""
    current_weather = CurrentWeather(
        city=weather_data['city'],
        main_condition=weather_data['main'],
        temperature=weather_data['temp'],
        feels_like=weather_data['feels_like'],
        timestamp=weather_data['timestamp'].date()
    )
    session.add(current_weather)
    session.commit()

def calculate_daily_aggregates():
    """Calculate and store daily weather aggregates."""
    today = datetime.now().date()
    for city in CITIES:
        weather_today = session.query(CurrentWeather).filter(CurrentWeather.city == city, CurrentWeather.timestamp == today).all()
        if weather_today:
            temps = [record.temperature for record in weather_today]
            conditions = [record.main_condition for record in weather_today]

            avg_temp = sum(temps) / len(temps)
            max_temp = max(temps)
            min_temp = min(temps)
            dominant_condition = max(set(conditions), key=conditions.count)  # Most frequent condition

            # Store in DailySummary
            existing_summary = session.query(DailySummary).filter(DailySummary.city == city, DailySummary.date == today).first()
            if not existing_summary:
                daily_summary = DailySummary(
                    city=city,
                    date=today,
                    avg_temp=avg_temp,
                    max_temp=max_temp,
                    min_temp=min_temp,
                    dominant_condition=dominant_condition
                )
                session.add(daily_summary)
                session.commit()

    st.success("Daily weather summaries have been updated.")

def check_for_alerts(weather):
    """Check if the weather data breaches the alert thresholds."""
    city = weather['city']
    temp = weather['temp']
    if temp > ALERT_THRESHOLD:
        consecutive_breach_count[city] += 1
        if consecutive_breach_count[city] >= TEMP_ALERT_CONSECUTIVE_COUNT:
            trigger_alert(weather)
            consecutive_breach_count[city] = 0  # Reset after alert
    else:
        consecutive_breach_count[city] = 0  # Reset if condition not met

def trigger_alert(weather):
    """Trigger an alert when thresholds are breached."""
    city = weather['city']
    temp = weather['temp']
    st.warning(f"ALERT: High temperature detected in {city}! Current temp: {temp:.2f}°C")
    # Optionally, send an email alert
    # send_email_alert(city, temp)

def send_email_alert(city, temperature):
    """Send an email alert (Optional)."""
    try:
        with SMTP("smtp.your-email-provider.com", 587) as smtp:
            smtp.starttls()
            smtp.login("your-email@example.com", "your-password")
            message = f"Subject: Weather Alert!\n\nTemperature in {city} has exceeded {ALERT_THRESHOLD}°C. Current temp: {temperature:.2f}°C."
            smtp.sendmail("from@example.com", "to@example.com", message)
        st.info(f"Email alert sent for {city}!")
    except Exception as e:
        st.error(f"Failed to send email alert: {e}")

# Initialize the weather_data_for_day dictionary
weather_data_for_day = {}

def get_weather_updates():
    """Fetch and process weather updates for all cities."""
    weather_list = []
    for city in CITIES:
        coordinates = fetch_coordinates(city)
        if coordinates:
            weather_data = fetch_weather_data(coordinates['lat'], coordinates['lon'], units='metric')
            if weather_data is not None:
                # Check for alert conditions
                check_for_alerts(weather_data)

                # Initialize the city in the weather_data_for_day dictionary if not present
                if city not in weather_data_for_day:
                    weather_data_for_day[city] = []  # Initialize with an empty list if the city is new

                # Collect weather data for daily summary
                weather_data_for_day[city].append(weather_data)

                # Store current weather data
                store_current_weather(weather_data)

                weather_list.append(weather_data)
    return weather_list


def get_weather_forecast_display(city):
    """Fetch and process forecast data for display."""
    coordinates = fetch_coordinates(city)  # Fetch coordinates for the city
    if coordinates:
        lat = coordinates['lat']
        lon = coordinates['lon']
        
        # Call fetch_weather_forecast with latitude and longitude
        forecast_data = fetch_weather_forecast(lat, lon)
        if forecast_data:
            forecast_df = pd.DataFrame(forecast_data)
            forecast_df['date'] = pd.to_datetime(forecast_df['date'])
            forecast_df['weekday'] = forecast_df['date'].dt.day_name()
            forecast_df['date_only'] = forecast_df['date'].dt.date

            # Get unique days for forecast
            unique_days = forecast_df['date_only'].unique()
            display_forecast = []

            for day in unique_days:
                day_data = forecast_df[forecast_df['date_only'] == day]
    
                avg_temp = day_data['temp'].mean() if not day_data['temp'].isnull().all() else None
                max_temp = day_data['temp'].max() if not day_data['temp'].isnull().all() else None
                min_temp = day_data['temp'].min() if not day_data['temp'].isnull().all() else None
                dominant_condition = day_data['main'].mode()[0] if not day_data['main'].empty else "Unknown"
                icon = day_data['icon'].mode()[0] if not day_data['icon'].empty else None

                display_forecast.append({
                    'weekday': day.strftime('%A'),
                    'avg_temp': f"{avg_temp:.2f}°C" if avg_temp is not None else "Data not available",
                    'max_temp': f"{max_temp:.2f}°C" if max_temp is not None else "Data not available",
                    'min_temp': f"{min_temp:.2f}°C" if min_temp is not None else "Data not available",
                    'main': dominant_condition,
                    'icon': icon
                })


            return display_forecast
    return None

# ----------------------------
# Streamlit UI Components
# ----------------------------

# Page Configuration
st.set_page_config(page_title="WeatherPro", layout="wide")

# Title and Subtitle
st.markdown("<h1 style='text-align: center;'>WeatherPro</h1>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center;'>🌦️ Real-Time Weather Monitoring System 🌦️</h2>", unsafe_allow_html=True)

# Sidebar for Alert Settings and User Preferences
st.sidebar.header("Alert Settings")
# Assuming ALERT_THRESHOLD is defined as a float
ALERT_THRESHOLD = st.sidebar.number_input("Temperature Alert Threshold (°C)", min_value=20.0, max_value=50.0, value=float(ALERT_THRESHOLD), step=0.5)

TEMP_ALERT_CONSECUTIVE_COUNT = st.sidebar.number_input("Consecutive Breaches for Alert", min_value=1, max_value=5, value=TEMP_ALERT_CONSECUTIVE_COUNT, step=1)

st.sidebar.header("User Preferences")
temp_unit = st.sidebar.selectbox("Select Temperature Unit", options=["Celsius", "Fahrenheit"], index=0)

# Convert temperature if user selects Fahrenheit
if temp_unit == "Fahrenheit":
    conversion_factor = 9/5
    conversion_offset = 32
else:
    conversion_factor = 1
    conversion_offset = 0

def convert_temp(temp):
    """Convert temperature from Celsius to desired unit."""
    if isinstance(temp, (int, float)):  # Check if temp is numeric
        return (temp * conversion_factor) + conversion_offset
    return None  # Return None for non-numeric inputs

# Input for adding new cities
st.sidebar.header("Manage Cities")
new_city = st.sidebar.text_input("Add a new city:")
if st.sidebar.button("Add City"):
    if new_city:
        if new_city.strip() not in CITIES:
            CITIES.append(new_city.strip())
            st.sidebar.success(f"{new_city.strip()} added to monitoring list!")
        else:
            st.sidebar.warning(f"{new_city.strip()} is already in the monitoring list.")
    else:
        st.sidebar.warning("Please enter a city name.")

# Display list of monitored cities with option to remove
if CITIES:
    st.sidebar.subheader("Monitored Cities")
    for city in CITIES:
        if st.sidebar.button(f"Remove {city}"):
            CITIES.remove(city)
            st.sidebar.success(f"{city} removed from monitoring list!")
            break  # To avoid RuntimeError for changing list size during iteration

# Display current weather updates
if CITIES:
    weather_updates = get_weather_updates()  # Get weather updates
    for weather in weather_updates:
        st.subheader(f"Weather in **{weather['city']}** ({weather['timestamp'].strftime('%A')})")  # Show current day

        # Load and display weather icon
        icon_url = f"http://openweathermap.org/img/wn/{weather['icon']}@2x.png"
        try:
            img = Image.open(BytesIO(requests.get(icon_url).content))
            st.image(img, width=100)
        except:
            st.write("Icon not available.")

        # Create a weather widget-like display with colors
        col1, col2, col3 = st.columns(3)
        with col1:
            temp_display = f"{convert_temp(weather['temp']):.2f}°{'F' if temp_unit == 'Fahrenheit' else 'C'}"
            st.metric(label="Temperature", value=temp_display, delta=None, help="Current temperature")
        with col2:
            feels_like_display = f"{convert_temp(weather['feels_like']):.2f}°{'F' if temp_unit == 'Fahrenheit' else 'C'}"
            st.metric(label="Feels Like", value=feels_like_display, delta=None, help="Feels like temperature")
        with col3:
            st.metric(label="Condition", value=weather['main'], delta=None, help="Weather condition")

        st.markdown(f"<p style='text-align: center;'>**Updated at:** {weather['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} </p>", unsafe_allow_html=True)
        st.write("---")

        # Fetch and display 5-day forecast
        forecast_data = get_weather_forecast_display(weather['city'])
        if forecast_data:
            st.subheader(f"5-Day Forecast for **{weather['city']}**")
            forecast_df = pd.DataFrame(forecast_data)

            # Convert temperatures based on user preference
            forecast_df['avg_temp'] = forecast_df['avg_temp'].apply(convert_temp)
            forecast_df['max_temp'] = forecast_df['max_temp'].apply(convert_temp)
            forecast_df['min_temp'] = forecast_df['min_temp'].apply(convert_temp)

            # Display forecast in a compact, widget-like format
            # Assuming `forecast_df` is your DataFrame containing the weather forecast data
            for _, row in forecast_df.iterrows():
                col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

                with col1:
                    st.write(f"**{row['weekday']}**")

                with col2:
                    # Check if avg_temp is None and fallback to current_temp
                    if row['avg_temp'] is not None:
                        st.write(f"Avg: {row['avg_temp']:.2f}°{'F' if temp_unit == 'Fahrenheit' else 'C'}")
                    # elif row['current_temp'] is not None:  # Fallback to current_temp if avg_temp is None
                        # st.write(f"Avg: {row['current_temp']:.2f}°{'F' if temp_unit == 'Fahrenheit' else 'C'}")
                    else:
                        st.write(f"Avg: {convert_temp(weather['temp']):.2f}°{'F' if temp_unit == 'Fahrenheit' else 'C'}")

                with col3:
                    # Check if max_temp is None and fallback to current_temp
                    if row['max_temp'] is not None:
                        st.write(f"Max: {row['max_temp']:.2f}°{'F' if temp_unit == 'Fahrenheit' else 'C'}")
                    # elif row['current_temp'] is not None:  # Fallback to current_temp if max_temp is None
                        # st.write(f"Max: {row['current_temp']:.2f}°{'F' if temp_unit == 'Fahrenheit' else 'C'}")
                    else:
                        st.write(f"Max: {convert_temp(weather['temp']):.2f}°{'F' if temp_unit == 'Fahrenheit' else 'C'}")

                    # Check if min_temp is None and fallback to current_temp
                    if row['min_temp'] is not None:
                        st.write(f"Min: {row['min_temp']:.2f}°{'F' if temp_unit == 'Fahrenheit' else 'C'}")
                    # elif row['current_temp'] is not None:  # Fallback to current_temp if min_temp is None
                        # st.write(f"Min: {row['current_temp']:.2f}°{'F' if temp_unit == 'Fahrenheit' else 'C'}")
                    else:
                        st.write(f"Min: {convert_temp(weather['temp']):.2f}°{'F' if temp_unit == 'Fahrenheit' else 'C'}")

                with col4:
                    try:
                        icon_url = f"http://openweathermap.org/img/wn/{row['icon']}@2x.png"
                        response = requests.get(icon_url)
                        response.raise_for_status()  # Raise an error for bad responses
                        img = Image.open(BytesIO(response.content))
                        st.image(img, width=50)
                    except Exception as e:
                        st.write("Icon not available.")
                        st.write(f"Error: {e}")  # Optional: Log the error for debugging

                st.write("---")

            else:
                st.write("No forecast data available.")


    # Display Daily Summaries
    st.header("Daily Weather Summaries")
    for city in CITIES:
        st.subheader(f"Daily Summary for **{city}**")
        today = datetime.now().date()
        summary = session.query(DailySummary).filter(DailySummary.city == city, DailySummary.date == today).first()
        if summary:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(label="Average Temp", value=f"{convert_temp(summary.avg_temp):.2f}°{'F' if temp_unit == 'Fahrenheit' else 'C'}")
            with col2:
                st.metric(label="Max Temp", value=f"{convert_temp(summary.max_temp):.2f}°{'F' if temp_unit == 'Fahrenheit' else 'C'}")
            with col3:
                st.metric(label="Min Temp", value=f"{convert_temp(summary.min_temp):.2f}°{'F' if temp_unit == 'Fahrenheit' else 'C'}")
            with col4:
                st.metric(label="Dominant Condition", value=summary.dominant_condition)
            st.write("---")
        else:
            st.write("No summary available for today yet.")

    # Visualizations: Historical Temperature Trends
    st.header("Historical Temperature Trends")
    for city in CITIES:
        st.subheader(f"Temperature Trend for **{city}**")
        history = session.query(DailySummary).filter(DailySummary.city == city).order_by(DailySummary.date).all()
        if history:
            history_df = pd.DataFrame([{
                'date': record.date,
                'avg_temp': convert_temp(record.avg_temp)
            } for record in history])

            st.line_chart(history_df.set_index('date'))
        else:
            st.write("No historical data available.")

    # Display Alerts (Logged within the main loop)

    # Daily aggregate calculation at midnight
    def daily_aggregation_job():
        calculate_daily_aggregates()

    scheduler.add_job(daily_aggregation_job, 'cron', hour=23, minute=59)  # Schedule daily at 23:59
    scheduler.add_job(get_weather_updates, 'interval', minutes=5)  # Call API every 5 minutes
    scheduler.start()

    # Clean up on app stop
    def shutdown():
        if scheduler.running:
            scheduler.shutdown()
            st.write("Scheduler has been shut down.")

    # Call shutdown manually at the end
    shutdown()
