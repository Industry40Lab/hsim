RESULTS_FOLDER = "hsim/GSOM/flask/static/results/"
RESULTS_FILENAME = "results.csv"
RESULTS_CSV = RESULTS_FOLDER + RESULTS_FILENAME

USERS_DB = "hsim/GSOM/flask/static/db/users.db"

# UPLOAD_FOLDER removed, uploads now use TEMP_FOLDER
ALLOWED_EXTENSIONS = {'xlsx'}

TEMP_FOLDER_NAME = 'simulation_results'

AZURE_CONNECTION_STRING = "endpoint=https://co-service.france.communication.azure.com/;accesskey=F2Ak856tysHa1vOGwxzeee8Lt8V0G64fMeNEYLuxzADw0qAUlVMBJQQJ99BDACULyCpC87VsAAAAAZCSZ8cL"  # Replace with your Azure connection string  

POLLER_WAIT_TIME = 15 # seconds