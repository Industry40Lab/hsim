from flask import Blueprint, render_template, session, redirect, url_for, request, flash, jsonify
import sqlite3
import os
from flask.cli import F
import pandas as pd

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


from hsim.GSOM.flask.config import USERS_DB, RESULTS_CSV

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

def delete_user(username):
    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()

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
    delete_user(username)
    flash(f"User '{username}' deleted.", "success")
    return redirect(url_for('admin.admin_page'))

@admin_bp.route('/delete_all_users', methods=['POST'])
def admin_delete_all_users():
    if session.get('username') != 'admin':
        return redirect(url_for('main.dashboard'))
    # Prevent deleting current user
    deleted_count = len(get_all_users()) - 1  # Exclude current user
    [delete_user(user['username']) for user in get_all_users() if user['username'] != session.get('username')]
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
