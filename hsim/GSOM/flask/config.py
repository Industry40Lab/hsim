RESULTS_FOLDER = "hsim/GSOM/flask/static/results/"
RESULTS_FILENAME = "results.csv"
RESULTS_CSV = RESULTS_FOLDER + RESULTS_FILENAME

USERS_DB = "hsim/GSOM/flask/static/db/users.db"

# UPLOAD_FOLDER removed, uploads now use TEMP_FOLDER
ALLOWED_EXTENSIONS = {'xlsx'}

TEMP_FOLDER_NAME = 'simulation_results'

# Security: Load sensitive data from environment variables
AZURE_EMAIL_CONNECTION_STRING = os.getenv("AZURE_EMAIL_CONNECTION_STRING", "")
if not AZURE_EMAIL_CONNECTION_STRING:
    logger.warning("AZURE_EMAIL_CONNECTION_STRING not set in environment variables")

# Azure Blob Storage connection string (for file storage)
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
if not AZURE_STORAGE_CONNECTION_STRING:
    logger.warning("AZURE_STORAGE_CONNECTION_STRING not set - files will be stored locally")

# Enable Azure Blob Storage (set to False to use local filesystem)
USE_AZURE_STORAGE = os.getenv("USE_AZURE_STORAGE", "True").lower() == "true" and bool(AZURE_STORAGE_CONNECTION_STRING)

POLLER_WAIT_TIME = 15 # seconds

USE_GANTT = True
TIMEOUT = 180 # seconds, max sim time