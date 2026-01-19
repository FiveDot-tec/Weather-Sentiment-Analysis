
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

