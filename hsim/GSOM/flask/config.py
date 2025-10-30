import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup logging
logger = logging.getLogger(__name__)

RESULTS_FOLDER = "hsim/GSOM/flask/static/results/"
RESULTS_FILENAME = "results.csv"
RESULTS_CSV = RESULTS_FOLDER + RESULTS_FILENAME

USERS_DB = os.getenv("USERS_DB", "hsim/GSOM/flask/static/db/users.db")

# UPLOAD_FOLDER removed, uploads now use TEMP_FOLDER
ALLOWED_EXTENSIONS = {'xlsx'}

TEMP_FOLDER_NAME = 'simulation_results'

# Security: Load sensitive data from environment variables
AZURE_CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING", "")
if not AZURE_CONNECTION_STRING:
    logger.warning("AZURE_CONNECTION_STRING not set in environment variables")

POLLER_WAIT_TIME = int(os.getenv("POLLER_WAIT_TIME", "15"))  # seconds

USE_GANTT = os.getenv("USE_GANTT", "True").lower() == "true"
TIMEOUT = int(os.getenv("TIMEOUT", "180"))  # seconds, max sim time