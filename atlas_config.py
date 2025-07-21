# atlas_config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
# This should be called once at the application's startup
load_dotenv()

def get_openrouter_api_key():
    """
    Retrieves the OpenRouter API key from environment variables.
    """
    return os.getenv("OPENROUTER_API_KEY")

# You might add other configuration getters here in the future
# def get_another_setting():
#     return os.getenv("ANOTHER_SETTING")
