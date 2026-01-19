"""
This module  configures a SQLite database, and initializes the
necessary directory structure for the weather sentiment data storage.

The logging configuration is loaded from a centralized configuration file to
ensure consistent log management. The SQLite database is created if it does
not exist, with the necessary table schema for storing weather and sentiment
data.

Attributes
----------
BASE_DIR : Path
    The root directory of the project.
log_config_path : Path
    The absolute path to the logging configuration file.
logger : logging.Logger
    Configured logger for the application.
db_path : Path
    The absolute path to the SQLite database file.
engine : Path
    Reference path for the SQLite database file.

Raises
------
OperationalError
    Raised if there is a failure in establishing a connection to the SQLite database
    or executing SQL commands during the initialization process.
"""
import logging.config
import os
from pathlib import Path
import sqlite3

# Calculate the project root (Annika_Abschlussproject)
BASE_DIR = Path(__file__).resolve().parent.parent
os.chdir(BASE_DIR)

# Use an absolute path for the config file to avoid working directory issues
log_config_path = BASE_DIR / "logging" / "logging_backend.ini"
logging.config.fileConfig(log_config_path, disable_existing_loggers=False)

logger = logging.getLogger()

# data storage with an sqlitedb engine

db_path = BASE_DIR / "data" / "output_data" / "weather_sentiment_data.db"

if not os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    logger.info("Database created successfully")
    conn.close()
else:
    logger.info("Database already exists")

conn = sqlite3.connect(db_path)  # Verbindung aufbauen

c = conn.cursor()  # Cursor erstellen

try:
    conn.execute("""CREATE TABLE IF NOT EXISTS weather_sentiment_data
    (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        city  text,
        temp float,
        description_en text,
        description_de text,
        sentiment_input text,
        polarity float,
        time datetime
    )""")
    logger.info("Table created successfully")
except: logger.info("Table already exists")

engine = db_path

