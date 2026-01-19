from textblob import TextBlob
from pathlib import Path
import os

import logging.config

# Calculate the project root 
BASE_DIR = Path(__file__).resolve().parent.parent
os.chdir(BASE_DIR)

# Use an absolute path for the config file to avoid working directory issues
log_config_path = BASE_DIR / "logging" / "logging_backend.ini"
logging.config.fileConfig(log_config_path, disable_existing_loggers=False)

logger = logging.getLogger()

class SentimentAnalysisWeather:
    def __init__(self, text_input: str):
        self.text_input = text_input or ""
        logger.debug("SentimentAnalysisWeather started")
        self.blob = TextBlob(self.text_input)
        self.means = 0

    def sentiment(self):
        if not self.blob.sentences:
            return
        for sentence in self.blob.sentences:
            logger.info(f"Sentence: {sentence} | Polarity: {sentence.sentiment.polarity}")
            self.means += sentence.sentiment.polarity

    def calc_total_polarity(self):
        num_sentences = len(self.blob.sentences)
        if num_sentences == 0:
            logger.warning("No sentences found to calculate polarity.")
            raise ZeroDivisionError("No sentences found to calculate polarity.")

        total_polarity =  self.means / len(self.blob.sentences)
        logger.info(f"Total Polarity: {total_polarity}")
        return total_polarity
