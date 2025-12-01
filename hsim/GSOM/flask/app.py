if __name__ == '__main__':
    import sys
    import os
    # Fix: Cross-platform way to add the "hsim" directory to sys.path
    abs_path = os.path.abspath(__file__)
    parts = abs_path.split(os.sep)
    if "hsim" in parts:
        hsim_index = parts.index("hsim")
        hsim_path = os.sep.join(parts[:hsim_index + 1])
        if hsim_path not in sys.path:
            sys.path.append(hsim_path)
            
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import sqlite3
import os
import shutil
import tempfile
from werkzeug.utils import secure_filename
import io
from threading import Thread
import atexit

# Import route modules
from hsim.GSOM.flask.routes.auth import auth_bp
from hsim.GSOM.flask.routes.main import main_bp
from hsim.GSOM.flask.routes.account import account_bp
from hsim.GSOM.flask.routes.admin import admin_bp

# Create Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure key in production

# Configure upload folder
from hsim.GSOM.flask.config import TEMP_FOLDER_NAME, USERS_DB, USE_AZURE_STORAGE, AZURE_STORAGE_CONNECTION_STRING
TEMP_FOLDER = os.path.join(tempfile.gettempdir(), TEMP_FOLDER_NAME)
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER  # No longer needed

# Ensure temp directory exists (still needed for local fallback)
os.makedirs(TEMP_FOLDER, exist_ok=True)

# Initialize Azure Blob Storage
if USE_AZURE_STORAGE:
    try:
        from hsim.GSOM.flask.azure_storage import init_storage
        init_storage(AZURE_STORAGE_CONNECTION_STRING)
        logger.info("Azure Blob Storage enabled and initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Azure Blob Storage: {e}")
        logger.warning("Falling back to local filesystem storage")
else:
    logger.info("Using local filesystem storage")

# Initialize SQLite database for user authentication
def init_db():
    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)
app.register_blueprint(account_bp)
app.register_blueprint(admin_bp)  # Register the admin blueprint

# Initialize database on startup
with app.app_context():
    init_db()

# Cleanup function to remove temporary files when the app shuts down
def cleanup_temp_files():
    if os.path.exists(TEMP_FOLDER):
        try:
            shutil.rmtree(TEMP_FOLDER)
            print(f"Cleaned up temporary directory: {TEMP_FOLDER}")
        except Exception as e:
            print(f"Error cleaning up temporary directory: {e}")

# Register the cleanup function to run on exit
atexit.register(cleanup_temp_files)

# Root route redirects to main page
@app.route('/')
def index():
    return redirect(url_for('main.dashboard'))

if __name__ == '__main__':
    app.run(debug=False)