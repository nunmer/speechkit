import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("API_KEY")
FOLDER_ID = os.environ.get("FOLDER_ID")

if not API_KEY:
    raise EnvironmentError("API_KEY is not set. Add it to your .env file.")
if not FOLDER_ID:
    raise EnvironmentError("FOLDER_ID is not set. Add it to your .env file.")
