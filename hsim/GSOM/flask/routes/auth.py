if __name__ == '__main__' or 'routes.main':
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

import time
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import sqlite3
import re
import smtplib
from email.mime.text import MIMEText
import random
import string
from werkzeug.security import generate_password_hash, check_password_hash
from azure.communication.email import EmailClient

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Email validation regex
EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
AZURE = True

# Password validation regex - at least 8 chars, 1 uppercase, 1 lowercase, 1 digit
PASSWORD_REGEX = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$"

from hsim.GSOM.flask.config import USERS_DB, AZURE_EMAIL_CONNECTION_STRING, POLLER_WAIT_TIME


def validate_password_strength(password):
    """
    Validate password strength.
    Requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit."
    return True, ""


# Database connection helper
def get_db_connection():
    conn = sqlite3.connect(USERS_DB)
    conn.row_factory = sqlite3.Row
    return conn

# Function to send email
def send_reset_email(email, username, new_password):
    if AZURE:
        return azure_reset_email(email, username, new_password)
    try:
        sender_email = "your_email@example.com"  # Replace with your email
        sender_password = "your_password"  # Replace with your email password
        smtp_server = "smtp.gmail.com"
        smtp_port = 587

        subject = "Password Reset Request"
        body = f"Hello {username},\n\nYour new password is: {new_password}\n\nPlease log in and change your password immediately."

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = email

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, msg.as_string())
        return True
    except Exception as e:
        flash(f"Failed to send email: {e}", "error")
        return False
    
def azure_reset_email(email, username, new_password):
    try:
        email_client = EmailClient.from_connection_string(AZURE_EMAIL_CONNECTION_STRING)  # Replace with your Azure connection string
        
        message = {
            "content": {
            "subject": "Password Reset Request",
            "plainText": f"Hello {username},\n\nYour new password is: {new_password}\n\nPlease log in and change your password immediately.",
            "html": f"<html><body><p>Hello {username},</p><p>Your new password is: <strong>{new_password}</strong></p><p>Please log in and change your password immediately.</p></body></html>"
            },
            "recipients": {
            "to": [
                {
                "address": email,
                "displayName": username
                }
            ]
            },
            "senderAddress": "<DoNotReply@1ec817b7-5abc-46b6-8a56-ada65744ba69.azurecomm.net>"
        }
        
        poller = email_client.begin_send(message)
        # Wait for the poller to complete, but with a timeout and error handling
        try:
            result = poller.result(timeout=POLLER_WAIT_TIME)  # Wait up to 15 seconds for completion
            # Optionally, check result.status or similar here
            return True
        except Exception as e:
            flash(f"Email send operation did not complete: {e}", "error")
            return False

    except Exception as e:
        flash(f"Failed to send email: {e}", "error")
        return False

# Login route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ?', 
            (username,)
        ).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['authenticated'] = True
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('auth/login.html')

# Register route
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validate input
        if not re.match(EMAIL_REGEX, email):
            flash('Invalid email format. Please enter a valid email.', 'error')
        elif password != confirm_password:
            flash('Passwords do not match. Please try again.', 'error')
        else:
            # Validate password strength
            is_valid, error_msg = validate_password_strength(password)
            if not is_valid:
                flash(error_msg, 'error')
            else:
                conn = get_db_connection()
                try:
                    hashed_password = generate_password_hash(password)
                    conn.execute(
                        'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                        (username, email, hashed_password)
                    )
                    conn.commit()
                    flash('Registration successful! Please log in.', 'success')
                    return redirect(url_for('auth.login'))
                except sqlite3.IntegrityError:
                    flash('Username or email already exists. Please try again.', 'error')
                finally:
                    conn.close()
    
    return render_template('auth/register.html')

# Forgot password route
@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        identifier = request.form['identifier']
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT username, email FROM users WHERE username = ? OR email = ?', 
            (identifier, identifier)
        ).fetchone()
        
        if user:
            username, email = user['username'], user['email']
            # Generate a random password
            new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
            hashed_password = generate_password_hash(new_password)
            
            conn.execute(
                'UPDATE users SET password = ? WHERE username = ?', 
                (hashed_password, username)
            )
            conn.commit()
            
            if send_reset_email(email, username, new_password):
                flash('A reset email has been sent to your email address.', 'success')
            else:
                flash('Failed to send reset email.', 'error')
        else:
            flash('No account found with the provided username or email.', 'error')
        
        conn.close()
    
    return render_template('auth/forgot_password.html')

# API endpoint to check if username exists
@auth_bp.route('/api/check_username', methods=['POST'])
def check_username():
    """API endpoint to check if username is available."""
    from flask import jsonify
    username = request.json.get('username', '').strip()

    if not username:
        return jsonify({'available': False, 'message': 'Username is required'})

    conn = get_db_connection()
    existing = conn.execute(
        'SELECT username FROM users WHERE username = ?',
        (username,)
    ).fetchone()
    conn.close()

    if existing:
        return jsonify({'available': False, 'message': 'Username already taken'})
    else:
        return jsonify({'available': True, 'message': 'Username is available'})

# API endpoint to check if email exists
@auth_bp.route('/api/check_email', methods=['POST'])
def check_email():
    """API endpoint to check if email is already registered."""
    from flask import jsonify
    email = request.json.get('email', '').strip()

    if not email:
        return jsonify({'valid': False, 'available': False, 'message': 'Email is required'})

    # Validate email format
    if not re.match(EMAIL_REGEX, email):
        return jsonify({'valid': False, 'available': False, 'message': 'Invalid email format'})

    conn = get_db_connection()
    existing = conn.execute(
        'SELECT email FROM users WHERE email = ?',
        (email,)
    ).fetchone()
    conn.close()

    if existing:
        return jsonify({'valid': True, 'available': False, 'message': 'Email already registered'})
    else:
        return jsonify({'valid': True, 'available': True, 'message': 'Email is available'})

# API endpoint to validate password
@auth_bp.route('/api/validate_password', methods=['POST'])
def validate_password_api():
    """API endpoint to validate password strength."""
    from flask import jsonify
    password = request.json.get('password', '')

    is_valid, error_msg = validate_password_strength(password)

    if is_valid:
        return jsonify({'valid': True, 'message': 'Password meets requirements'})
    else:
        return jsonify({'valid': False, 'message': error_msg})

# Logout route
@auth_bp.route('/logout')
def logout():
    session.pop('authenticated', None)
    session.pop('username', None)
    session.pop('result_filename', None)
    session.pop('simulation_success', None)
    session.pop('task_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))