"""
This module configures logging and loads a JSON configuration file for further processing.

The module sets up logging parameters from a logging configuration file and attempts
to load a JSON configuration file. It handles errors related to file loading and logs
appropriate messages for success or failure.

Attributes
----------
logger : logging.Logger
    The logger object used for logging events across the backend app.

config_data : dict
    The configuration data loaded from the JSON configuration file. This dictionary
    contains key-value pairs specific to the application's settings.

Raises
------
FileNotFoundError
    If the specified JSON configuration file is not found.
Exception
    For any other errors occurring during the JSON configuration file loading process.
    """

import logging.config
import json
import os
from pathlib import Path

os.chdir(Path(__file__).parent.parent)


logging.config.fileConfig("./logging/logging_backend.ini")

logger = logging.getLogger()

# Read Config.JSON
try:
    with open("./config/config.json", mode = "r", encoding="UTF_8") as file:
        config_data = json.load(file)
        logger.info("File leaded: config.json")
except FileNotFoundError:
    logger.error("Config File not found")
except Exception as e:
    logger.error(f"Error loading config file: {e}")
    
# Store config values in global variables
LGS = config_data.get("lgs", [])