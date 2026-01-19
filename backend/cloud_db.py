"""
This module establishes a connection to a Supabase database, initializes a logging
configuration, and provides a class to interact with the database via API calls.

The module calculates the project's base directory and sets up consistent logging
using a defined configuration file. It also provides functionality for securely
loading environment variables to establish a connection to a Supabase instance
for database operations.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client
import logging.config

# Calculate the project root 
BASE_DIR = Path(__file__).resolve().parent.parent
os.chdir(BASE_DIR)

# Use an absolute path for the config file to avoid working directory issues
log_config_path = BASE_DIR / "logging" / "logging_backend.ini"
logging.config.fileConfig(log_config_path, disable_existing_loggers=False)

logger = logging.getLogger()
class CloudDB:
    def __init__(self):
        # Load environment variables upon initialization
        load_dotenv()
        url :str = os.getenv("SUPABASE_URL", "")
        key : str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

        if not url or not key:
            raise ValueError("Supabase URL or Key not found in environment variables.")

        # Initialize the client instance here
        self.client: Client = create_client(url, key)

    def insert_sentiment_record(self, data: dict):
        """
        Inserts a sentiment record into the specified database table. The function
        communicates with a Supabase client to perform the insertion and verifies
        the operation's success. If unsuccessful, an error is logged, and an
        exception is raised.

        :param data: The record data to be inserted into the `owm_sentiment` table.
        :type data: dict
        :return: The first inserted row data upon successful insertion.
        :rtype: dict
        :raises RuntimeError: If the insertion operation fails.
        """
        table_name = "owm_sentiment"

        # Supabase handles 'id' (if UUID) and 'created_at' automatically
        res = self.client.table(table_name).insert(data).execute()

        if not res.data:
            logger.error(f"Insert data into {table_name} failed: {res.error}")
            raise RuntimeError(f"Insert data into {table_name} failed: {res.error}")

        logger.info(f"Successfully inserted record into {table_name}.")
        return res.data[0]  # Return the first inserted row data