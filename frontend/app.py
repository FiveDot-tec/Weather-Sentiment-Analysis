"""
This Streamlit application provides a web interface for performing weather data requests and conducting sentiment
analysis based on user feedback. It interacts with a FastAPI backend and optionally sends notifications to a Discord
webhook. The interface enables users to request weather information for a specific city, view the results, provide
feedback on the weather, and analyze the sentiment of the feedback.

Attributes:
    BASE_DIR (Path): The base directory of the project, used to resolve file paths.
    URL (str): The Discord webhook URL loaded from the environment variables.
    HEADERS (dict): HTTP headers used for API requests, including User-Agent and Content-Type.

Supported functionalities:
    - Request the current weather based on user-provided city name.
    - Display the city weather data, including temperature and descriptions in English and German.
    - Gather user feedback regarding the weather and process its sentiment through FastAPI.
    - Log events and optionally send logs/notifications to a Discord channel.
    - Persist session state, enabling continuous data and UI availability during interactions.

Logging is configured via a centralized logging configuration file for consistent and detailed logging behavior.
"""

# streamlit run frontend/app.py --server.port 8501
import os
from pathlib import Path
import requests
from dotenv import load_dotenv
import streamlit as st
import logging.config
from datetime import datetime
from io import BytesIO



# Calculate the project root 
BASE_DIR = Path(__file__).resolve().parent.parent

# Use an absolute path for the config file to avoid working directory issues
log_config_path = BASE_DIR / "logging" / "logging_frontend.ini"
logging.config.fileConfig(log_config_path, disable_existing_loggers=False)

logger = logging.getLogger()


#tests of Iris Prediction Model are going to be sent to discord
load_dotenv()
URL = os.getenv("WEB_HOOK")
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json"
}

def inject_css():
    st.markdown(
        """
        <style>
        .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1100px; }
        .card {
            border: 1px solid rgba(49, 51, 63, 0.2);
            border-radius: 16px;
            padding: 18px 18px;
            background: rgba(255,255,255,0.03);
            margin-bottom: 1rem;
        }
        .small-muted { opacity: 0.75; font-size: 0.9rem; }
        </style>
        """,
        unsafe_allow_html=True
    )



# Configure webpage
def main():
    """
    Main function to initialize session state, set up a user interface for weather data requests,
    and perform sentiment analysis of user feedback. This function interacts with a FastAPI backend
    for data processing and uses web requests to communicate between the frontend and backend. It
    also provides real-time feedback and displays relevant data in the Streamlit interface.

    :raises Exception: If an error occurs during an HTTP request to the backend or Discord webhook.

    :return: None
    """
    st.set_page_config(
        page_title="Weather Sentiment Analysis",
        page_icon="🌤️",
        layout="centered",
        initial_sidebar_state="expanded"
    )
    inject_css()
    
    
    #  INITIALIZE SESSION STATE KEYS
    if "weather_result" not in st.session_state:
        st.session_state.weather_result = None
    if "weather_city" not in st.session_state:
        st.session_state.weather_city = ""
    if "sentiment_result" not in st.session_state:
        st.session_state.sentiment_result = None
    # Create the Web interface - Design
    # Title
    st.title("🌤️ Weather Request & Sentiment Analysis App")
    # Subtitle
    st.subheader("Weather data request and sentiment analysis of user feelings about the weather.")

    # Input row
    c1, c2 = st.columns([3, 1], vertical_alignment="bottom")

    with c1:
        city_name = st.text_input(
            "City",
            placeholder="Berlin",
            label_visibility="collapsed"
        )

    with c2:
        request_clicked = st.button("🔎 Request", use_container_width=True)

    # HTTP client logic to send the ImageID to the FastAPI backend
    backend_url = "127.0.0.1"
    backend_port = "8000"


    # A button to Request!
    if request_clicked and city_name:

        payload = {"city_name": city_name}
        logger.info(f"Name of requested City: {city_name}")
        # configure timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            # Sending request to FastAPI
            response = requests.post(f"http://{backend_url}:{backend_port}/request", json=payload, headers=HEADERS)

            if response.status_code == 200:
                st.session_state.weather_result = response.json()
                st.session_state.weather_city = city_name
                data = {"content": f"Data returned successfully for request {city_name} at {timestamp}"}
                if URL:
                    response_discord = requests.post(URL, json=data, headers=HEADERS)
                    logger.info(f"Discord: {response_discord.status_code}")
            else:
                st.error(f"Error: {response.reason}")
                logger.error(f"Error: {response.reason}")
                data = {"content": f"Request for {city_name} failed {timestamp}"}
                if URL:
                    response_discord = requests.post(URL, json=data, headers=HEADERS)
                    logger.info(f"Discord: {response_discord.status_code}")

        except Exception as e:
            st.error(f"An error occurred: {e}")
            logger.error(f"An error occurred: {e}")
            data = {"content": f"An error occurred: {e} at {timestamp}"}
            if URL:
                response_discord = requests.post(URL, json=data, headers=HEADERS)
                logger.info(f"Discord: {response_discord.status_code}")

    # PERSISTENT WEATHER DISPLAY
    if st.session_state.weather_result:
        res = st.session_state.weather_result


        c1, c2, c3 = st.columns([1, 2, 3], vertical_alignment="center")

        # Column 1 — Weather icon
        with c1:
            icon_code = res.get("icon")
            if icon_code:
                # 1. Construct the internal URL (Backend-to-Backend)
                icon_url = f"http://{backend_url}:{backend_port}/icon/{icon_code}"

                try:
                    # 2. Fetch the actual image data from your FastAPI backend
                    response = requests.get(icon_url, timeout=5)
                    if response.status_code == 200:
                        # 3. Pass the raw bytes (response.content) to st.image
                        st.image(response.content, width=90)
                    else:
                        st.markdown("<h1>clear sky</h1>", unsafe_allow_html=True)
                except Exception as e:
                    logger.error(f"Frontend failed to fetch icon from backend: {e}")
                    st.markdown("<h1>🌦️</h1>", unsafe_allow_html=True)
            else:
                st.markdown("<h1>🌦️</h1>", unsafe_allow_html=True)


        # Column 2 — Temperature
        with c2:
            st.metric(
                label="🌡️ Temperature",
                value=f"{res['temp']} °C"
            )

        # Column 3 — Descriptions
        with c3:
            st.markdown(
                f"""
                **📍 {st.session_state.weather_city}**

                **English:** {res['description_en']}  
                **German:** {res['description_de']}
                """
            )

        # --- FEEDBACK SECTION (Only visible after weather result exists) ---
    if st.session_state.weather_result:
        st.divider()
        feedback = st.text_area(
        "How do you feel about this weather?",
        placeholder="Short, natural feedback works best.",
        height=100,
        label_visibility="collapsed"
    )

        # configure timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if st.button("Submit Feedback"):
            payload = {"text": feedback,
                       "city_name": st.session_state.weather_city}
            logger.info("Feedback submitted")
            try:
                response = requests.post(f"http://{backend_url}:{backend_port}/sentiment", json=payload, headers=HEADERS)
                logger.info(f"Sentiment analysis: {response.reason}")

                if response.status_code == 200:
                    result = response.json()
                    st.session_state.sentiment_result = result.get("polarity")
                    logger.info(f"Sentiment analysis: {result}")
                else:
                    st.error(f"Error: {response.reason}")
                    logger.error(f"Error: {response.reason}")

            except Exception as e:
                logger.error(f"Error: {e}")



            data = {"content": f"User feedback: {feedback} at {timestamp}"}
            if URL:
                response_discord = requests.post(URL, json=data, headers=HEADERS)
                logger.info(f"Discord: {response_discord.status_code}")

    if st.session_state.sentiment_result is not None:
        score = st.session_state.sentiment_result

        # 2 Column layout
        c1, c2 = st.columns([1, 2], vertical_alignment="center")

        #c1: Sentiment Analysis Result: Polarity
        with c1:
            st.metric(
                label="Sentiment Analysis Result:",
                value=score
            )

        #c2: Sentiment Analysis Icon scale

        with c2:
             # simple interpretation “pill”
            if score > 0.2:
                st.success(f"😊 Positive sentiment (polarity: {score:.1f})")
            elif score < -0.2:
                st.error(f"☹️ Negative sentiment (polarity: {score:.1f})")
            else:
                st.info(f"😐 Neutral sentiment (polarity: {score:.1f})")




if __name__ == "__main__":
    logger.info("Starting Streamlit Frontend Application")
    main()
    logger.info("Streamlit Frontend Application Finished")