from flask import Blueprint, render_template, session, redirect, url_for, request, flash, jsonify
import sqlite3
import os
import shutil
from flask.cli import F
import pandas as pd
import logging

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

logger = logging.getLogger(__name__)

from hsim.GSOM.flask.config import USERS_DB, RESULTS_CSV, USE_AZURE_STORAGE

if USE_AZURE_STORAGE:
    from hsim.GSOM.flask.azure_storage import get_storage

def get_db_connection():
    conn = sqlite3.connect(USERS_DB)
    conn.row_factory = sqlite3.Row
    return conn

def get_all_users():
    conn = get_db_connection()
    users = conn.execute("SELECT username, email FROM users").fetchall()
    conn.close()
    return users

def update_user(old_username, new_username, new_email):
    conn = get_db_connection()
    conn.execute(
        "UPDATE users SET username = ?, email = ? WHERE username = ?",
        (new_username, new_email, old_username)
    )
    conn.commit()
    conn.close()

def delete_all_user_files(username):
    """
    Delete all files (temp and workspace) for a specific user.
    Works with both Azure Blob Storage and local filesystem.

    Args:
        username: Username whose files should be deleted

    Returns:
        Number of files deleted
    """
    total_deleted = 0

    try:
        if USE_AZURE_STORAGE:
            # Delete from Azure Blob Storage
            storage = get_storage()
            total_deleted = storage.delete_all_user_files(username)
            logger.info(f"Deleted {total_deleted} Azure files for user {username}")
        else:
            # Delete from local filesystem
            import tempfile
            from hsim.GSOM.flask.config import TEMP_FOLDER_NAME

            # Delete temp files
            temp_folder = os.path.join(tempfile.gettempdir(), TEMP_FOLDER_NAME)
            if os.path.exists(temp_folder):
                temp_files = [f for f in os.listdir(temp_folder)
                             if f.startswith(f"{username}_")]
                for file in temp_files:
                    try:
                        os.remove(os.path.join(temp_folder, file))
                        total_deleted += 1
                        logger.debug(f"Deleted temp file: {file}")
                    except Exception as e:
                        logger.warning(f"Failed to delete temp file {file}: {e}")

            # Delete user workspace files
            user_folder = os.path.join('hsim', 'GSOM', 'flask', 'static', 'user_results', username)
            if os.path.exists(user_folder):
                try:
                    files_count = len([f for f in os.listdir(user_folder) if os.path.isfile(os.path.join(user_folder, f))])
                    shutil.rmtree(user_folder)
                    total_deleted += files_count
                    logger.info(f"Deleted user folder: {user_folder} ({files_count} files)")
                except Exception as e:
                    logger.error(f"Failed to delete user folder {user_folder}: {e}")

            logger.info(f"Deleted {total_deleted} local files for user {username}")

    except Exception as e:
        logger.error(f"Error deleting files for user {username}: {e}")

    return total_deleted

def delete_user(username):
    """
    Delete a user account and all associated files.

    Args:
        username: Username to delete
    """
    # First delete all user files
    files_deleted = delete_all_user_files(username)

    # Then delete user from database
    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()

    logger.info(f"Deleted user '{username}' and {files_deleted} associated files")

def get_results():
    if os.path.exists(RESULTS_CSV):
        df = pd.read_csv(RESULTS_CSV)
        return df.to_dict('records')
    return []

def delete_result(index):
    if os.path.exists(RESULTS_CSV):
        df = pd.read_csv(RESULTS_CSV)
        if 0 <= index < len(df):
            df = df.drop(index)
            df.to_csv(RESULTS_CSV, index=False)

def delete_all_results():
    if os.path.exists(RESULTS_CSV):
        os.remove(RESULTS_CSV)

@admin_bp.route('/', methods=['GET'])
def admin_page():
    if session.get('username') != 'admin':
        return redirect(url_for('main.dashboard'))
    users = get_all_users()
    results = get_results()
    return render_template('admin.html', users=users, results=results)

@admin_bp.route('/delete_user/<username>', methods=['POST'])
def admin_delete_user(username):
    if session.get('username') != 'admin':
        return redirect(url_for('main.dashboard'))
    # Prevent deleting current user
    if username == session.get('username'):
        flash("You cannot delete your own account while logged in.", "warning")
        return redirect(url_for('admin.admin_page'))

    # Delete user and get file count
    files_deleted = delete_all_user_files(username)

    # Delete user from database
    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()

    if files_deleted > 0:
        flash(f"User '{username}' and {files_deleted} associated file(s) deleted.", "success")
    else:
        flash(f"User '{username}' deleted.", "success")
    return redirect(url_for('admin.admin_page'))

@admin_bp.route('/delete_all_users', methods=['POST'])
def admin_delete_all_users():
    if session.get('username') != 'admin':
        return redirect(url_for('main.dashboard'))

    # Get all users except current admin
    users_to_delete = [user for user in get_all_users() if user['username'] != session.get('username')]
    deleted_count = len(users_to_delete)
    total_files_deleted = 0

    # Delete each user and their files
    for user in users_to_delete:
        files_deleted = delete_all_user_files(user['username'])
        total_files_deleted += files_deleted

        # Delete user from database
        conn = get_db_connection()
        conn.execute("DELETE FROM users WHERE username = ?", (user['username'],))
        conn.commit()
        conn.close()

    if total_files_deleted > 0:
        flash(f"Deleted {deleted_count} user(s) and {total_files_deleted} associated file(s). Current user was not deleted.", "success")
    else:
        flash(f"Deleted {deleted_count} user(s). Current user was not deleted.", "success")
    return redirect(url_for('admin.admin_page'))

@admin_bp.route('/update_user/<username>', methods=['POST'])
def admin_update_user(username):
    if session.get('username') != 'admin':
        return redirect(url_for('main.dashboard'))
    new_username = request.form.get('new_username')
    new_email = request.form.get('new_email')
    update_user(username, new_username, new_email)
    flash(f"User '{username}' updated.", "success")
    return redirect(url_for('admin.admin_page'))

@admin_bp.route('/delete_result/<int:index>', methods=['POST'])
def admin_delete_result(index):
    if session.get('username') != 'admin':
        return redirect(url_for('main.dashboard'))
    delete_result(index)
    flash(f"Result {index} deleted.", "success")
    return redirect(url_for('admin.admin_page'))

@admin_bp.route('/delete_all_results', methods=['POST'])
def admin_delete_all_results():
    if session.get('username') != 'admin':
        return redirect(url_for('main.dashboard'))
    delete_all_results()
    flash("All results deleted.", "success")
    return redirect(url_for('admin.admin_page'))

@admin_bp.route('/delete_selected_results', methods=['POST'])
def admin_delete_selected_results():
    if session.get('username') != 'admin':
        return redirect(url_for('main.dashboard'))
    selected = request.form.getlist('selected_results')
    if selected:
        import pandas as pd
        import os
        if os.path.exists(RESULTS_CSV):
            df = pd.read_csv(RESULTS_CSV)
            # Convert selected indices to int and sort descending to avoid index shift
            indices = sorted([int(i) for i in selected], reverse=True)
            for idx in indices:
                if 0 <= idx < len(df):
                    df = df.drop(df.index[idx])
            df.to_csv(RESULTS_CSV, index=False)
        flash(f"Deleted {len(selected)} result(s).", "success")
    else:
        flash("No results selected.", "warning")
    return redirect(url_for('admin.admin_page'))
