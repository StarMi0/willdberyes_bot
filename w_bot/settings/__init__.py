import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
API_TOKEN = os.getenv("API_TOKEN")
BEARER_TOKEN = os.getenv('BEARER_TOKEN')
