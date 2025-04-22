from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import sqlite3
import os
from werkzeug.utils import secure_filename
import io
from threading import Thread
import tempfile

# Import route modules
from routes.auth import auth_bp
from routes.main import main_bp
from routes.account import account_bp

# Create Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure key in production

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize SQLite database for user authentication
def init_db():
    conn = sqlite3.connect("users.db")
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

# Initialize database on startup
with app.app_context():
    init_db()

# Root route redirects to main page
@app.route('/')
def index():
    return redirect(url_for('main.dashboard'))

if __name__ == '__main__':
    app.run(debug=True)