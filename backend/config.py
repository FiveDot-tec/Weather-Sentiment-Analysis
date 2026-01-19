"""
A script for initializing logging configuration and loading configuration data
from a JSON file.

This script sets up logging using a specified configuration file and attempts
to read configuration data from a `config.json` file. Global variables
are defined based on the retrieved configuration values. If the configuration
file is missing or an error occurs during loading, appropriate logging messages
are created.

Global Variables
----------------
LGS : list
    A list of languages or configurations retrieved from the `config.json` file.
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