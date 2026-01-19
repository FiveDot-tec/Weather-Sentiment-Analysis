"""
Module for managing weather data requests and sentiment analysis.

This module provides an API for fetching weather data based on a city name and performing
sentiment analysis on user feedback associated with weather conditions. The module also stores
weather and sentiment data in both a cloud database and a local SQLite database.

Classes:
    WeatherRequest: A model for a weather request containing a city name.
    SentimentRequest: A model for a sentiment analysis request containing text and the corresponding city name.

Routes:
    /request: Fetches weather data for a specified city, stores it temporarily, and returns weather details.
    /sentiment: Performs sentiment analysis on user feedback and stores results with corresponding weather data.
"""
# fastapi dev backend/app.py --reload --port 8000
import sys
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException 
from fastapi.responses import Response
import logging.config
import requests
from sentiment_analysis import SentimentAnalysisWeather 
from dotenv import load_dotenv # type: ignore
from cloud_db import CloudDB
import sqlite3
import sqlite_db as sqldb
import pandas as pd # type: ignore
from datetime import datetime
from weather_fetcher import WeatherRequest, SentimentRequest
import config as cfg

# Calculate the project root 
BASE_DIR = Path(__file__).resolve().parent.parent
os.chdir(BASE_DIR)

# Use an absolute path for the config file to avoid working directory issues
log_config_path = BASE_DIR / "logging" / "logging_backend.ini"
logging.config.fileConfig(log_config_path, disable_existing_loggers=False)

logger = logging.getLogger()

# Create the app
app = FastAPI(title="WeatherSentimentsAPP", description="Weather data request and sentiment analysis of user")

#Initialize DB
db = CloudDB()
TEMP_WEATHER_STORE = {}




# API key for OpenWeatherMap:
load_dotenv()
OWM_API_KEY = os.getenv("OWM_API_KEY")


@app.get("/icon/{icon_code}")
def get_icon(icon_code: str):
    url = f"https://openweathermap.org/img/wn/{icon_code}@2x.png"
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()

        # Debug (keep for now)
        logger.info(
            f"ICON DEBUG: code={icon_code} status={r.status_code} "
            f"content_type={r.headers.get('Content-Type')} bytes={len(r.content)} "
            f"first8={r.content[:8]!r}"
        )

        # PNG files always start with b'\x89PNG\r\n\x1a\n'
        if not r.content.startswith(b"\x89PNG\r\n\x1a\n"):
            raise HTTPException(status_code=502, detail="Icon response was not a PNG")

        return Response(content=r.content, media_type="image/png")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Icon fetch failed for {icon_code}: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch weather icon")



# fetch weather data from API based on city_name
@app.post("/request")
async def get_weather(request: WeatherRequest):
    """
    Handles a weather request for a specified city and fetches current weather
    information in both English and German from the OpenWeatherMap API. The weather
    data includes the city name, temperature, and descriptions in two different
    languages.

    :param request: An instance of `WeatherRequest` containing the `city_name` for
        which the weather information is requested.
    :type request: WeatherRequest
    :return: A dictionary containing the city name, temperature, description in
        English, and description in German.
    :rtype: dict
    :raises HTTPException: If an error occurs while fetching weather data from the
        API or if the JSON structure from the API response is malformed.
    """
    city =request.city_name.lower()
    logger.info(f"Received weather request for city: {city}")
    
    weather_data = {}
    # URL for the weather API:
    for lg in cfg.LGS:
        WEATHER_API_URL = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OWM_API_KEY}&units=metric&lang={lg}"
        response = requests.get(WEATHER_API_URL)
        logger.info(f"Response from API: {response.text}")
        

        if response.status_code != 200:
            logger.error(f"Error fetching English weather data: {response.text}")
            raise HTTPException(status_code=response.status_code, detail=f"Error fetching weather data: {response.json().get('message', 'Unknown error')}")
        
        weather_data[lg] = response.json()

    try:
        name = weather_data["en"]["name"]
        temp = weather_data["en"]["main"]["temp"]
        description_en = weather_data["en"]["weather"][0]["description"]
        description_de = weather_data["de"]["weather"][0]["description"]
        icon = weather_data["en"]["weather"][0]["icon"]
    except KeyError as e:
        logger.error(f"Unexpected JSON structure from API: {e}")
        raise HTTPException(status_code=500, detail="Error processing weather data structure")

    TEMP_WEATHER_STORE[city] = {
        "city": city,
        "temp": temp,
        "description_en": description_en,
        "description_de": description_de,
    }
    logger.info(f"DEBUG icon code returned: {icon}")

    # Return the requested city name and weather data as a JSON response
    return {"name": name,
            "temp": temp,
            "description_en": description_en,
            "description_de": description_de,
            "icon": icon,
            }

# perform sentiment analysis on weather data
@app.post("/sentiment")
async def get_sentiment(request: SentimentRequest):
    """
    Handles sentiment analysis and integrates weather data to store combined results
    in both Supabase and SQLite database. Processes feedback text and associated
    city name to generate a sentiment score and combine it with weather data
    retrieved for the specified city. The combined result is saved and returned.

    :param request: The request object containing user feedback and city name
                    from the API request.
    :type request: SentimentRequest
    :raises HTTPException: If the weather data for the given city name is not
                           found in the temporary store.
    :return: A dictionary containing the calculated sentiment polarity score.
    :rtype: dict
    """
    user_feedback = request.text
    city_name = request.city_name.lower()

    sentiment_analysis = SentimentAnalysisWeather(request.text)
    sentiment_analysis.sentiment()
    sentiment_score = sentiment_analysis.calc_total_polarity()

    # Retrieve the temporary weather data using the city name key
    weather_data = TEMP_WEATHER_STORE.get(city_name)
    if not weather_data:
        raise HTTPException(status_code=404, detail=f"Weather data for {city_name} not found in temporary store.")

    # Final payload assembly matching the Supabase table schema
    final_db_payload = {
        **weather_data,  # Unpack the stored weather data
        "sentiment_input": user_feedback,  # Add feedback
        "polarity": sentiment_score  # Add polarity
    }

    # Insert into Supabase
    try:
        db.insert_sentiment_record(final_db_payload)
        logger.info(f"Successfully inserted record for {city_name} into Supabase.")
    except (ValueError, RuntimeError) as e:
        logger.error(f"DB Insert failed: {e}")

    df = pd.DataFrame([final_db_payload])
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # add timestamp to dataframe
    df['time'] = timestamp

    # Insert into sqlite file
    try:
        with sqlite3.connect(sqldb.engine) as conn:
            df.to_sql(
                name="weather_sentiment_data",
                con=conn,
                if_exists='append',
                index=False
            )
        logger.info(f"Successfully inserted record for {city_name} into sqlite file.")
    except (ValueError, RuntimeError) as e:
        logger.error(f"SQLITE Insert failed: {e}")

    # Return the sentiment score to the frontend
    return {"polarity": sentiment_score}