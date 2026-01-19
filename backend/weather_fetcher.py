"""
This module contains data models for processing requests related to weather
information and sentiment analysis. It utilizes Pydantic's BaseModel to
facilitate data validation and serialization.

The module defines:
- WeatherRequest: A model for weather-related requests, requiring the name of
  the city in the payload.
- SentimentRequest: A model for text-based sentiment analysis requests,
  including the text content and an associated city name.
"""
from pydantic import BaseModel
# structure of json payload
class WeatherRequest(BaseModel):
    """
    Represents a model for a weather request.

    This class is used for constructing a weather request model with information
    regarding the city for which the weather data is being requested.

    :ivar city_name: Name of the city for which the weather data is requested.
    :type city_name: str
    """
    city_name: str

class SentimentRequest(BaseModel):
    """
    Represents a sentiment request containing text to analyze and the related city name.

    This class is utilized to encapsulate the textual data for sentiment analysis along
    with the city name associated with that text. It serves as a data container for
    sentiment analysis input.

    :ivar text: The text content for which sentiment analysis will be performed.
    :type text: str
    :ivar city_name: The name of the city related to the text content.
    :type city_name: str
    """
    text: str
    city_name: str