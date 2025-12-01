if __name__ == '__main__' or 'routes.main':
    import sys
    import os
    abs_path = os.path.abspath(__file__)
    parts = abs_path.split(os.sep)
    if "hsim" in parts:
        hsim_index = parts.index("hsim")
        hsim_path = os.sep.join(parts[:hsim_index + 1])
        if hsim_path not in sys.path:
            sys.path.append(hsim_path)

from unittest import result
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file, jsonify, send_from_directory, abort
import sqlite3
import pandas as pd
import os
import io
import uuid
import tempfile
from werkzeug.utils import secure_filename
from concurrent.futures import ThreadPoolExecutor

from hsim.GSOM.backend import runner
from hsim.GSOM.flask.config import USERS_DB, TIMEOUT  # Import the same backend used in the Streamlit app

main_bp = Blueprint('main', __name__)

# Configure upload settings
from hsim.GSOM.flask.config import RESULTS_FOLDER as FOLDER, TEMP_FOLDER_NAME, USE_GANTT, USE_AZURE_STORAGE
TEMP_FOLDER = os.path.join(tempfile.gettempdir(), TEMP_FOLDER_NAME)
ALLOWED_EXTENSIONS = {'xlsx'}

# Create temporary directory if it doesn't exist
os.makedirs(TEMP_FOLDER, exist_ok=True)

# Import Azure storage utilities
if USE_AZURE_STORAGE:
    from hsim.GSOM.flask.azure_storage import get_storage, AzureBlobStorage

# Global executor for running simulations asynchronously
executor = ThreadPoolExecutor(max_workers=3)

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
    """Clean up old session files for the user (Excel, HTML, uploaded files)."""
    try:
        if USE_AZURE_STORAGE:
            # Clean up from Azure Blob Storage
            storage = get_storage()
            storage.clean_user_temp_files(username)
        else:
            # Clean up from local filesystem - remove all files starting with username_
            user_files = [f for f in os.listdir(TEMP_FOLDER)
                          if f.startswith(f"{username}_")]
            for file in user_files:
                try:
                    os.remove(os.path.join(TEMP_FOLDER, file))
                    logger.debug(f"Removed temp file: {file}")
                except Exception as e:
                    logger.warning(f"Failed to remove temp file {file}: {e}")
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

            # Save the output
            if USE_AZURE_STORAGE:
                # Upload to Azure Blob Storage
                storage = get_storage()
                storage.upload_file(
                    output.getvalue(),
                    result_filename,
                    storage.TEMP_CONTAINER
                )
            else:
                # Save to local filesystem
                result_path = os.path.join(TEMP_FOLDER, result_filename)
                with open(result_path, 'wb') as f:
                    f.write(output.getvalue())

            res = {
                'success': True,
                'processed_data': processed_data,
                'result_filename': result_filename
            }

            if USE_GANTT and "GANTT" in processed_data:
                gantt_filename = f"{username}_{uuid.uuid4().hex}.html"
                gantt_data = processed_data["GANTT"]

                if USE_AZURE_STORAGE:
                    # Upload Gantt chart to Azure
                    storage = get_storage()
                    storage.upload_file(
                        gantt_data.encode('utf-8'),
                        gantt_filename,
                        storage.TEMP_CONTAINER,
                        content_type='text/html'
                    )
                else:
                    # Save to local filesystem
                    gantt_path = os.path.join(TEMP_FOLDER, gantt_filename)
                    with open(gantt_path, 'w', encoding="utf-8") as f:
                        f.write(gantt_data)

                res['gantt_filename'] = gantt_filename

            return res
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
    
    if session.get('simulation_failed',False):
        flash('Simulation failed!', 'error')
        session.pop('simulation_failed', None)
    
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
        if 'uploaded_filename' in session:
            session.pop('uploaded_filename', None)
        
        # Save the uploaded file to TEMP_FOLDER with a unique name
        filename = secure_filename(file.filename)
        unique_filename = f"{username}_{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(TEMP_FOLDER, unique_filename)
        file.save(file_path)
        session['uploaded_filename'] = unique_filename  # Store in session
        
        task = executor.submit(run_simulation_task, file_path, username)
                  
        import time
        try:
            start_time = time.time()
            while not task.done() and (time.time() - start_time) < TIMEOUT:
                time.sleep(1)
            if not task.done():
                raise TimeoutError("Simulation timed out.")
        except TimeoutError as e:
            flash(str(e), 'error')
            # Optionally, cancel the task if possible
            return redirect(url_for('main.dashboard'))
        finally:
            session["simulation_success"] = task.done() and task.result().get('success', False)
            session["simulation_failed"] = "error" in task.result() and not session["simulation_success"]
            session["result_filename"] = task.result().get('result_filename')
            session["gantt_filename"] = task.result().get('gantt_filename',None)

            # Clean up the uploaded input file (no longer needed after simulation)
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"Removed uploaded input file: {unique_filename}")
            except Exception as e:
                logger.warning(f"Failed to remove uploaded input file: {e}")

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

    result_filename = session.get('result_filename')

    try:
        if USE_AZURE_STORAGE:
            # Download from Azure Blob Storage
            storage = get_storage()
            output = storage.download_file_stream(result_filename, storage.TEMP_CONTAINER)
        else:
            # Read from local filesystem
            result_path = os.path.join(TEMP_FOLDER, result_filename)
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
    except FileNotFoundError:
        flash('Result file not found', 'error')
        return redirect(url_for('main.dashboard'))
    except Exception as e:
        logger.error(f"Error downloading results: {e}")
        flash('Error downloading file', 'error')
        return redirect(url_for('main.dashboard'))

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
    result_filename = session.get('result_filename')
    safe_name = "".join(c for c in save_name if c.isalnum() or c in (' ', '_', '-')).rstrip()

    try:
        if USE_AZURE_STORAGE:
            # Azure Blob Storage version
            storage = get_storage()

            # Download file from temp container
            file_data = storage.download_file(result_filename, storage.TEMP_CONTAINER)

            # Check if file with same name exists (versioning logic)
            existing_files = storage.list_user_files(username, storage.USER_RESULTS_CONTAINER)
            base_name = safe_name
            version = 1

            import re
            def get_next_version_azure(fname, files_list):
                pattern = re.compile(rf"^{re.escape(base_name)}(?: v(\d+))?\.xlsx$")
                max_v = 0
                for f in files_list:
                    m = pattern.match(f)
                    if m:
                        v = m.group(1)
                        if v:
                            max_v = max(max_v, int(v))
                        else:
                            max_v = max(max_v, 0)
                return max_v + 1

            final_filename = f"{safe_name}.xlsx"
            if final_filename in existing_files:
                v_match = re.match(r"^(.*) v(\d+)$", safe_name)
                if v_match:
                    base_name = v_match.group(1)
                    version = int(v_match.group(2)) + 1
                else:
                    version = get_next_version_azure(safe_name, existing_files)
                safe_name_versioned = f"{base_name} v{version}"
                final_filename = f"{safe_name_versioned}.xlsx"
                while final_filename in existing_files:
                    version += 1
                    safe_name_versioned = f"{base_name} v{version}"
                    final_filename = f"{safe_name_versioned}.xlsx"

            # Upload to user results container
            storage.upload_file(file_data, final_filename, storage.USER_RESULTS_CONTAINER, username)
            flash('Results saved to your personal space!', 'success')

        else:
            # Local filesystem version
            result_path = os.path.join(TEMP_FOLDER, result_filename)
            if not os.path.exists(result_path):
                flash('Result file not found', 'error')
                return redirect(url_for('main.dashboard'))

            # Save to user-specific folder
            user_results_folder = os.path.join('hsim', 'GSOM', 'flask', 'static', 'user_results', username)
            os.makedirs(user_results_folder, exist_ok=True)

            # Versioning logic
            base_name = safe_name
            version = 1
            import re
            def get_next_version(fname, folder):
                pattern = re.compile(rf"^{re.escape(base_name)}(?: v(\d+))?\.xlsx$")
                max_v = 0
                for f in os.listdir(folder):
                    m = pattern.match(f)
                    if m:
                        v = m.group(1)
                        if v:
                            max_v = max(max_v, int(v))
                        else:
                            max_v = max(max_v, 0)
                return max_v + 1

            dest_path = os.path.join(user_results_folder, f"{safe_name}.xlsx")
            if os.path.exists(dest_path):
                v_match = re.match(r"^(.*) v(\d+)$", safe_name)
                if v_match:
                    base_name = v_match.group(1)
                    version = int(v_match.group(2)) + 1
                else:
                    version = get_next_version(safe_name, user_results_folder)
                safe_name_versioned = f"{base_name} v{version}"
                dest_path = os.path.join(user_results_folder, f"{safe_name_versioned}.xlsx")
                while os.path.exists(dest_path):
                    version += 1
                    safe_name_versioned = f"{base_name} v{version}"
                    dest_path = os.path.join(user_results_folder, f"{safe_name_versioned}.xlsx")

            import shutil
            shutil.copyfile(result_path, dest_path)
            flash('Results saved to your personal space!', 'success')

    except Exception as e:
        logger.error(f"Error saving results: {e}")
        flash(f'Failed to save results: {e}', 'error')

    return redirect(url_for('main.dashboard'))

@main_bp.route('/workspace')
def workspace():
    if not session.get('authenticated'):
        return redirect(url_for('auth.login'))
    username = session.get('username')
    files = []

    try:
        if USE_AZURE_STORAGE:
            # Get files from Azure Blob Storage
            storage = get_storage()
            files = storage.list_user_files(username, storage.USER_RESULTS_CONTAINER)
        else:
            # Get files from local filesystem
            user_results_folder = os.path.join('hsim', 'GSOM', 'flask', 'static', 'user_results', username)
            if os.path.exists(user_results_folder):
                for fname in os.listdir(user_results_folder):
                    if fname.endswith('.xlsx'):
                        files.append(fname)
    except Exception as e:
        logger.error(f"Error listing workspace files: {e}")
        flash('Error loading workspace files', 'error')

    is_admin = username == 'admin'
    all_user_files = {}

    if is_admin:
        try:
            if USE_AZURE_STORAGE:
                # Get all users' files from Azure
                storage = get_storage()
                container_client = storage.blob_service_client.get_container_client(storage.USER_RESULTS_CONTAINER)
                blobs = container_client.list_blobs()

                for blob in blobs:
                    # Parse username from blob path (format: username/filename)
                    if '/' in blob.name:
                        user, filename = blob.name.split('/', 1)
                        if user not in all_user_files:
                            all_user_files[user] = []
                        if filename.endswith('.xlsx'):
                            all_user_files[user].append(filename)
            else:
                # Get all users' files from local filesystem
                base_folder = os.path.join('hsim', 'GSOM', 'flask', 'static', 'user_results')
                if os.path.exists(base_folder):
                    for user in os.listdir(base_folder):
                        user_folder = os.path.join(base_folder, user)
                        if os.path.isdir(user_folder):
                            user_files = [f for f in os.listdir(user_folder) if f.endswith('.xlsx')]
                            if user_files:
                                all_user_files[user] = user_files
        except Exception as e:
            logger.error(f"Error listing all users' files for admin: {e}")

    return render_template('main/workspace.html', files=files, username=username, is_admin=is_admin, all_user_files=all_user_files)

@main_bp.route('/workspace/download/<filename>')
def workspace_download(filename):
    if not session.get('authenticated'):
        return redirect(url_for('auth.login'))
    username = session.get('username')

    try:
        if USE_AZURE_STORAGE:
            # Download from Azure Blob Storage
            storage = get_storage()
            file_stream = storage.download_file_stream(filename, storage.USER_RESULTS_CONTAINER, username)
            return send_file(
                file_stream,
                as_attachment=True,
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            # Download from local filesystem
            user_results_folder = os.path.join('hsim', 'GSOM', 'flask', 'static', 'user_results', username)
            return send_from_directory(user_results_folder, filename, as_attachment=True)
    except FileNotFoundError:
        flash('File not found', 'error')
        return redirect(url_for('main.workspace'))
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        flash('Error downloading file', 'error')
        return redirect(url_for('main.workspace'))

@main_bp.route('/workspace/delete/<filename>', methods=['POST'])
def workspace_delete(filename):
    if not session.get('authenticated'):
        return redirect(url_for('auth.login'))
    username = session.get('username')

    try:
        if USE_AZURE_STORAGE:
            # Delete from Azure Blob Storage
            storage = get_storage()
            success = storage.delete_file(filename, storage.USER_RESULTS_CONTAINER, username)
            if success:
                flash(f"Deleted '{filename}'", "success")
            else:
                flash("File not found.", "error")
        else:
            # Delete from local filesystem
            user_results_folder = os.path.join('hsim', 'GSOM', 'flask', 'static', 'user_results', username)
            file_path = os.path.join(user_results_folder, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                flash(f"Deleted '{filename}'", "success")
            else:
                flash("File not found.", "error")
    except Exception as e:
        logger.error(f"Error deleting file: {e}")
        flash("Error deleting file", "error")

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

    safe_new_name = "".join(c for c in new_name if c.isalnum() or c in (' ', '_', '-')).rstrip() + '.xlsx'

    try:
        if USE_AZURE_STORAGE:
            # Rename in Azure Blob Storage
            storage = get_storage()
            success = storage.rename_file(filename, safe_new_name, storage.USER_RESULTS_CONTAINER, username)
            if success:
                flash(f"Renamed to '{safe_new_name}'", "success")
            else:
                flash("File not found.", "error")
        else:
            # Rename in local filesystem
            user_results_folder = os.path.join('hsim', 'GSOM', 'flask', 'static', 'user_results', username)
            old_path = os.path.join(user_results_folder, filename)
            new_path = os.path.join(user_results_folder, safe_new_name)
            if os.path.exists(old_path):
                os.rename(old_path, new_path)
                flash(f"Renamed to '{safe_new_name}'", "success")
            else:
                flash("File not found.", "error")
    except Exception as e:
        logger.error(f"Error renaming file: {e}")
        flash("Error renaming file", "error")

    return redirect(url_for('main.workspace'))

# Admin: download any user's file
@main_bp.route('/workspace/admin/download/<user>/<filename>')
def admin_workspace_download(user, filename):
    if session.get('username') != 'admin':
        return redirect(url_for('main.dashboard'))

    try:
        if USE_AZURE_STORAGE:
            # Download from Azure Blob Storage
            storage = get_storage()
            file_stream = storage.download_file_stream(filename, storage.USER_RESULTS_CONTAINER, user)
            return send_file(
                file_stream,
                as_attachment=True,
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            # Download from local filesystem
            user_results_folder = os.path.join('hsim', 'GSOM', 'flask', 'static', 'user_results', user)
            return send_from_directory(user_results_folder, filename, as_attachment=True)
    except Exception as e:
        logger.error(f"Error downloading file for admin: {e}")
        flash('Error downloading file', 'error')
        return redirect(url_for('main.workspace'))

# Admin: delete any user's file
@main_bp.route('/workspace/admin/delete/<user>/<filename>', methods=['POST'])
def admin_workspace_delete(user, filename):
    if session.get('username') != 'admin':
        return redirect(url_for('main.dashboard'))

    try:
        if USE_AZURE_STORAGE:
            # Delete from Azure Blob Storage
            storage = get_storage()
            success = storage.delete_file(filename, storage.USER_RESULTS_CONTAINER, user)
            if success:
                flash(f"Deleted '{filename}' for user '{user}'", "success")
            else:
                flash("File not found.", "error")
        else:
            # Delete from local filesystem
            user_results_folder = os.path.join('hsim', 'GSOM', 'flask', 'static', 'user_results', user)
            file_path = os.path.join(user_results_folder, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                flash(f"Deleted '{filename}' for user '{user}'", "success")
            else:
                flash("File not found.", "error")
    except Exception as e:
        logger.error(f"Error deleting file for admin: {e}")
        flash("Error deleting file", "error")

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

    safe_new_name = "".join(c for c in new_name if c.isalnum() or c in (' ', '_', '-')).rstrip() + '.xlsx'

    try:
        if USE_AZURE_STORAGE:
            # Rename in Azure Blob Storage
            storage = get_storage()
            success = storage.rename_file(filename, safe_new_name, storage.USER_RESULTS_CONTAINER, user)
            if success:
                flash(f"Renamed '{filename}' to '{safe_new_name}' for user '{user}'", "success")
            else:
                flash("File not found.", "error")
        else:
            # Rename in local filesystem
            user_results_folder = os.path.join('hsim', 'GSOM', 'flask', 'static', 'user_results', user)
            old_path = os.path.join(user_results_folder, filename)
            new_path = os.path.join(user_results_folder, safe_new_name)
            if os.path.exists(old_path):
                os.rename(old_path, new_path)
                flash(f"Renamed '{filename}' to '{safe_new_name}' for user '{user}'", "success")
            else:
                flash("File not found.", "error")
    except Exception as e:
        logger.error(f"Error renaming file for admin: {e}")
        flash("Error renaming file", "error")

    return redirect(url_for('main.workspace'))

@main_bp.route('/gantt')    
def gantt():
    if not session.get('authenticated'):
        return redirect(url_for('auth.login'))
    gantt_file = session.get('gantt_filename')
    if not gantt_file:
        flash("No Gantt chart available.", "error")
        return redirect(url_for('main.dashboard'))
    return render_template('main/gantt.html', gantt_file=gantt_file)

@main_bp.route('/gantt_file')
def gantt_file():
    if not session.get('authenticated'):
        return redirect(url_for('auth.login'))
    gantt_filename = session.get('gantt_filename')
    if not gantt_filename:
        abort(404)

    try:
        if USE_AZURE_STORAGE:
            # Download from Azure Blob Storage
            storage = get_storage()
            file_stream = storage.download_file_stream(gantt_filename, storage.TEMP_CONTAINER)
            return send_file(file_stream, mimetype='text/html')
        else:
            # Read from local filesystem
            gantt_path = os.path.join(TEMP_FOLDER, gantt_filename)
            if not os.path.exists(gantt_path):
                abort(404)
            return send_file(gantt_path, mimetype='text/html')
    except FileNotFoundError:
        abort(404)
    except Exception as e:
        logger.error(f"Error loading Gantt chart: {e}")
        abort(500)