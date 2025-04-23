if __name__ == '__main__' or 'routes.main':
    import sys
    import os
    sys.path.append("//".join(os.path.abspath(__file__).split("\\")[:os.path.abspath(__file__).split("\\").index("hsim")+1]))

from unittest import result
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file, jsonify, send_from_directory
import sqlite3
import pandas as pd
import os
import io
import uuid
import tempfile
from werkzeug.utils import secure_filename
from concurrent.futures import ThreadPoolExecutor
from hsim.GSOM.backend import runner
from hsim.GSOM.flask.config import USERS_DB  # Import the same backend used in the Streamlit app

main_bp = Blueprint('main', __name__)

# Configure upload settings
from hsim.GSOM.flask.config import UPLOAD_FOLDER, RESULTS_FOLDER as FOLDER, TEMP_FOLDER_NAME
TEMP_FOLDER = os.path.join(tempfile.gettempdir(), TEMP_FOLDER_NAME)
ALLOWED_EXTENSIONS = {'xlsx'}

# Create temporary directory if it doesn't exist
os.makedirs(TEMP_FOLDER, exist_ok=True)

# Global executor for running simulations asynchronously
executor = ThreadPoolExecutor(max_workers=3)
simulation_tasks = {}

# Check if file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Database connection helper
def get_db_connection():
    conn = sqlite3.connect(USERS_DB)
    conn.row_factory = sqlite3.Row
    return conn

# Function to clean up old result files for a user
def clean_user_temp_files(username):
    try:
        user_files = [f for f in os.listdir(TEMP_FOLDER) 
                      if f.startswith(f"{username}_") and f.endswith(".xlsx")]
        for file in user_files:
            os.remove(os.path.join(TEMP_FOLDER, file))
    except Exception as e:
        print(f"Error cleaning up files: {e}")

# Function to run simulation in background
def run_simulation_task(file_path, username):
    try:
        with open(file_path, 'rb') as file:
            # Use the same runner function from the Streamlit app
            processed_data, output = runner(file, username)
            
            # Generate unique filename for this result
            result_filename = f"{username}_{uuid.uuid4().hex}.xlsx"
            result_path = os.path.join(TEMP_FOLDER, result_filename)
            
            # Save the output to a file
            with open(result_path, 'wb') as f:
                f.write(output.getvalue())
            
            return {
                'success': True,
                'processed_data': processed_data,
                'result_filename': result_filename
            }
    except Exception as e:
        print(f"Simulation error: {e}")  # Log the error for debugging
        return {
            'success': False,
            'error': str(e)
        }

# Dashboard/home route
@main_bp.route('/dashboard')
def dashboard():
    if not session.get('authenticated'):
        return redirect(url_for('auth.login'))  
    if not session.get('result_filename'):
        pass
    username = session.get('username')
    
    # Debug current session state
    print(f"Session state: simulation_success={session.get('simulation_success')}, result_filename={session.get('result_filename')}")
    
    # Check if there's a completed simulation task
    task_id = session.get('task_id')
    if task_id and task_id in simulation_tasks:
        if simulation_tasks[task_id].done():
            result = simulation_tasks[task_id].result()
            print(f"Task completed with result: {result}")  # Debug log
            
            if result.get('success', False):
                flash('Simulation completed successfully!', 'success')
                # Set session variables
                session['simulation_success'] = True
                session['result_filename'] = result.get('result_filename')
                # Force session save
                session.modified = True
                print(f"Updated session: simulation_success={session.get('simulation_success')}, result_filename={session.get('result_filename')}")
            else:
                flash(f"An error occurred: {result.get('error', 'Unknown error')}", 'error')
                session['simulation_success'] = False
                session.modified = True
            
            # Remove the task from our dictionary to avoid checking it again
            simulation_tasks.pop(task_id)
            session.pop('task_id', None)
    
    # Try to load leaderboard data
    try:
        results_df = pd.read_csv(FOLDER+"results.csv", header=0)
        leaderboard_data = results_df.to_dict('records')
    except FileNotFoundError:
        leaderboard_data = []
    
    return render_template(
        'main/dashboard.html',
        username=username,
        leaderboard_data=leaderboard_data,
        simulation_success=session.get('simulation_success', False),
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
        username = session.get('username')
        
        # Clean up any existing temporary files for this user
        clean_user_temp_files(username)
        session['simulation_success'] = False
        if 'result_filename' in session:
            session.pop('result_filename', None)
        
        # Save the uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        task = executor.submit(run_simulation_task, file_path, username)
                  
        import time
        try:
            timeout = 30  # seconds
            start_time = time.time()
            while not task.done() and (time.time() - start_time) < timeout:
                time.sleep(0.5)
            if not task.done():
                raise TimeoutError("Simulation timed out.")
        except TimeoutError as e:
            flash(str(e), 'error')
            # Optionally, cancel the task if possible
            session.pop('task_id', None)
            return redirect(url_for('main.dashboard'))
        finally:
            session["simulation_success"] = task.done()
            session["result_filename"] = task.result().get('result_filename')

        return redirect(url_for('main.dashboard'))
    
    flash('Invalid file type. Please upload an Excel (.xlsx) file.', 'error')
    return redirect(url_for('main.dashboard'))

# Download results route
@main_bp.route('/download_results')
def download_results():
    if not session.get('authenticated'):
        return redirect(url_for('auth.login'))
    
    if not session.get('simulation_success') or not session.get('result_filename'):
        flash('No simulation results available for download', 'error')
        return redirect(url_for('main.dashboard'))
    
    result_path = os.path.join(TEMP_FOLDER, session.get('result_filename'))
    if not os.path.exists(result_path):
        flash('Result file not found', 'error')
        return redirect(url_for('main.dashboard'))
    output = open(result_path, 'rb')
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
        results_df = pd.read_csv(FOLDER+"results.csv", header=0)
        leaderboard_data = results_df.to_dict('records')
    except FileNotFoundError:
        leaderboard_data = []
    
    return render_template('main/leaderboard.html', leaderboard_data=leaderboard_data)

@main_bp.route('/set_session_var', methods=['POST'])
def set_session_var():
    if not session.get('authenticated'):
        return jsonify({'success': False}), 401
    data = request.get_json()
    # Example: set a session variable named 'simulation_running'
    session['simulation_success'] = data.get('simulation_success', True)
    return jsonify({'success': True})

@main_bp.route('/save_results', methods=['POST'])
def save_results():
    if not session.get('authenticated'):
        return redirect(url_for('auth.login'))
    if not session.get('simulation_success') or not session.get('result_filename'):
        flash('No simulation results available to save', 'error')
        return redirect(url_for('main.dashboard'))

    save_name = request.form.get('save_name', '').strip()
    if not save_name:
        flash('Please provide a name to save the results.', 'error')
        return redirect(url_for('main.dashboard'))

    username = session.get('username')
    result_path = os.path.join(TEMP_FOLDER, session.get('result_filename'))
    if not os.path.exists(result_path):
        flash('Result file not found', 'error')
        return redirect(url_for('main.dashboard'))

    # Save to user-specific folder
    user_results_folder = os.path.join('hsim', 'GSOM', 'flask', 'static', 'user_results', username)
    os.makedirs(user_results_folder, exist_ok=True)
    safe_name = "".join(c for c in save_name if c.isalnum() or c in (' ', '_', '-')).rstrip()
    dest_path = os.path.join(user_results_folder, f"{safe_name}.xlsx")
    try:
        import shutil
        shutil.copyfile(result_path, dest_path)
        flash('Results saved to your personal space!', 'success')
    except Exception as e:
        flash(f'Failed to save results: {e}', 'error')

    return redirect(url_for('main.dashboard'))

@main_bp.route('/workspace')
def workspace():
    if not session.get('authenticated'):
        return redirect(url_for('auth.login'))
    username = session.get('username')
    user_results_folder = os.path.join('hsim', 'GSOM', 'flask', 'static', 'user_results', username)
    files = []
    if os.path.exists(user_results_folder):
        for fname in os.listdir(user_results_folder):
            if fname.endswith('.xlsx'):
                files.append(fname)
    is_admin = username == 'admin'
    all_user_files = {}
    if is_admin:
        base_folder = os.path.join('hsim', 'GSOM', 'flask', 'static', 'user_results')
        if os.path.exists(base_folder):
            for user in os.listdir(base_folder):
                user_folder = os.path.join(base_folder, user)
                if os.path.isdir(user_folder):
                    user_files = [f for f in os.listdir(user_folder) if f.endswith('.xlsx')]
                    if user_files:
                        all_user_files[user] = user_files
    return render_template('main/workspace.html', files=files, username=username, is_admin=is_admin, all_user_files=all_user_files)

@main_bp.route('/workspace/download/<filename>')
def workspace_download(filename):
    if not session.get('authenticated'):
        return redirect(url_for('auth.login'))
    username = session.get('username')
    user_results_folder = os.path.join('hsim', 'GSOM', 'flask', 'static', 'user_results', username)
    return send_from_directory(user_results_folder, filename, as_attachment=True)

@main_bp.route('/workspace/delete/<filename>', methods=['POST'])
def workspace_delete(filename):
    if not session.get('authenticated'):
        return redirect(url_for('auth.login'))
    username = session.get('username')
    user_results_folder = os.path.join('hsim', 'GSOM', 'flask', 'static', 'user_results', username)
    file_path = os.path.join(user_results_folder, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        flash(f"Deleted '{filename}'", "success")
    else:
        flash("File not found.", "error")
    return redirect(url_for('main.workspace'))

@main_bp.route('/workspace/rename/<filename>', methods=['POST'])
def workspace_rename(filename):
    if not session.get('authenticated'):
        return redirect(url_for('auth.login'))
    username = session.get('username')
    new_name = request.form.get('new_name', '').strip()
    if not new_name:
        flash("New name cannot be empty.", "error")
        return redirect(url_for('main.workspace'))
    user_results_folder = os.path.join('hsim', 'GSOM', 'flask', 'static', 'user_results', username)
    old_path = os.path.join(user_results_folder, filename)
    safe_new_name = "".join(c for c in new_name if c.isalnum() or c in (' ', '_', '-')).rstrip() + '.xlsx'
    new_path = os.path.join(user_results_folder, safe_new_name)
    if os.path.exists(old_path):
        os.rename(old_path, new_path)
        flash(f"Renamed to '{safe_new_name}'", "success")
    else:
        flash("File not found.", "error")
    return redirect(url_for('main.workspace'))

# Admin: download any user's file
@main_bp.route('/workspace/admin/download/<user>/<filename>')
def admin_workspace_download(user, filename):
    if session.get('username') != 'admin':
        return redirect(url_for('main.dashboard'))
    user_results_folder = os.path.join('hsim', 'GSOM', 'flask', 'static', 'user_results', user)
    return send_from_directory(user_results_folder, filename, as_attachment=True)

# Admin: delete any user's file
@main_bp.route('/workspace/admin/delete/<user>/<filename>', methods=['POST'])
def admin_workspace_delete(user, filename):
    if session.get('username') != 'admin':
        return redirect(url_for('main.dashboard'))
    user_results_folder = os.path.join('hsim', 'GSOM', 'flask', 'static', 'user_results', user)
    file_path = os.path.join(user_results_folder, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        flash(f"Deleted '{filename}' for user '{user}'", "success")
    else:
        flash("File not found.", "error")
    return redirect(url_for('main.workspace'))

# Admin: rename any user's file
@main_bp.route('/workspace/admin/rename/<user>/<filename>', methods=['POST'])
def admin_workspace_rename(user, filename):
    if session.get('username') != 'admin':
        return redirect(url_for('main.dashboard'))
    new_name = request.form.get('new_name', '').strip()
    if not new_name:
        flash("New name cannot be empty.", "error")
        return redirect(url_for('main.workspace'))
    user_results_folder = os.path.join('hsim', 'GSOM', 'flask', 'static', 'user_results', user)
    old_path = os.path.join(user_results_folder, filename)
    safe_new_name = "".join(c for c in new_name if c.isalnum() or c in (' ', '_', '-')).rstrip() + '.xlsx'
    new_path = os.path.join(user_results_folder, safe_new_name)
    if os.path.exists(old_path):
        os.rename(old_path, new_path)
        flash(f"Renamed '{filename}' to '{safe_new_name}' for user '{user}'", "success")
    else:
        flash("File not found.", "error")
    return redirect(url_for('main.workspace'))