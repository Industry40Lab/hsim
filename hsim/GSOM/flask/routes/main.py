from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
import sqlite3
import pandas as pd
import os
import io
from werkzeug.utils import secure_filename
from concurrent.futures import ThreadPoolExecutor

if __name__ == '__main__' or 'routes.main':
    import sys
    sys.path.append("//".join(os.path.abspath(__file__).split("\\")[:os.path.abspath(__file__).split("\\").index("hsim")+1]))

from hsim.GSOM.backend import runner  # Import the same backend used in the Streamlit app

main_bp = Blueprint('main', __name__)

# Configure upload settings
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx'}

# Global executor for running simulations asynchronously
executor = ThreadPoolExecutor(max_workers=3)
simulation_tasks = {}

# Check if file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Database connection helper
def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

# Function to run simulation in background
def run_simulation_task(file_path, username):
    try:
        with open(file_path, 'rb') as file:
            # Use the same runner function from the Streamlit app
            processed_data, output = runner(file, username)
            
            # Store results in session
            return {
                'success': True,
                'processed_data': processed_data,
                'download_data': output.getvalue()
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

# Dashboard/home route
@main_bp.route('/dashboard')
def dashboard():
    if not session.get('authenticated'):
        return redirect(url_for('auth.login'))
    
    username = session.get('username')
    
    # Check if there's a completed simulation task
    task_id = session.get('task_id')
    if task_id and task_id in simulation_tasks:
        if simulation_tasks[task_id].done():
            result = simulation_tasks[task_id].result()
            if result['success']:
                flash('Simulation completed successfully!', 'success')
                session['simulation_success'] = True
                session['download_data'] = result['download_data']
            else:
                flash(f"An error occurred: {result['error']}", 'error')
                session['simulation_success'] = False
    
    # Try to load leaderboard data
    try:
        results_df = pd.read_csv("results.csv", header=0)
        leaderboard_data = results_df.to_dict('records')
    except FileNotFoundError:
        leaderboard_data = []
    
    return render_template(
        'main/dashboard.html',
        username=username,
        leaderboard_data=leaderboard_data,
        simulation_success=session.get('simulation_success', False)
    )

# File upload and simulation running route
@main_bp.route('/run_simulation', methods=['POST'])
def run_simulation():
    if not session.get('authenticated'):
        return redirect(url_for('auth.login'))
    
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('main.dashboard'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('main.dashboard'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Start simulation in background
        username = session.get('username')
        task = executor.submit(run_simulation_task, file_path, username)
        
        # Store task for later retrieval
        task_id = str(id(task))
        simulation_tasks[task_id] = task
        session['task_id'] = task_id
        
        flash('Simulation started. This may take a moment...', 'info')
        return redirect(url_for('main.dashboard'))
    
    flash('Invalid file type. Please upload an Excel (.xlsx) file.', 'error')
    return redirect(url_for('main.dashboard'))

# Download results route
@main_bp.route('/download_results')
def download_results():
    if not session.get('authenticated'):
        return redirect(url_for('auth.login'))
    
    if not session.get('simulation_success') or not session.get('download_data'):
        flash('No simulation results available for download', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Create a BytesIO object from the stored data
    output = io.BytesIO(session.get('download_data'))
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name='simulation_results.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# Leaderboard route
@main_bp.route('/leaderboard')
def leaderboard():
    if not session.get('authenticated'):
        return redirect(url_for('auth.login'))
    
    try:
        results_df = pd.read_csv("results.csv", header=0)
        leaderboard_data = results_df.to_dict('records')
    except FileNotFoundError:
        leaderboard_data = []
    
    return render_template('main/leaderboard.html', leaderboard_data=leaderboard_data)