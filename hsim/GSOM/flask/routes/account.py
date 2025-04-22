from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import sqlite3
import re

account_bp = Blueprint('account', __name__, url_prefix='/account')

# Email validation regex
EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

# Database connection helper
def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

# Account profile route
@account_bp.route('/profile')
def profile():
    if not session.get('authenticated'):
        return redirect(url_for('auth.login'))
    
    username = session.get('username')
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('auth.logout'))
    
    return render_template('account/profile.html', user=user)

# Change password route
@account_bp.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if not session.get('authenticated'):
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_new_password = request.form['confirm_new_password']
        
        if new_password != confirm_new_password:
            flash('New passwords do not match. Please try again.', 'error')
            return redirect(url_for('account.change_password'))
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT password FROM users WHERE username = ?', 
            (session.get('username'),)
        ).fetchone()
        
        if user and user['password'] == old_password:
            conn.execute(
                'UPDATE users SET password = ? WHERE username = ?', 
                (new_password, session.get('username'))
            )
            conn.commit()
            flash('Password updated successfully!', 'success')
            return redirect(url_for('account.profile'))
        else:
            flash('Old password is incorrect. Please try again.', 'error')
        
        conn.close()
    
    return render_template('account/change_password.html')

# Change email route
@account_bp.route('/change_email', methods=['GET', 'POST'])
def change_email():
    if not session.get('authenticated'):
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        new_email = request.form['new_email']
        confirm_new_email = request.form['confirm_new_email']
        
        if new_email != confirm_new_email:
            flash('Emails do not match. Please try again.', 'error')
            return redirect(url_for('account.change_email'))
        
        if not re.match(EMAIL_REGEX, new_email):
            flash('Invalid email format. Please enter a valid email.', 'error')
            return redirect(url_for('account.change_email'))
        
        conn = get_db_connection()
        try:
            conn.execute(
                'UPDATE users SET email = ? WHERE username = ?', 
                (new_email, session.get('username'))
            )
            conn.commit()
            flash('Email updated successfully!', 'success')
            return redirect(url_for('account.profile'))
        except sqlite3.IntegrityError:
            flash('This email is already in use. Please try a different one.', 'error')
        finally:
            conn.close()
    
    return render_template('account/change_email.html')

# Change username route
@account_bp.route('/change_username', methods=['GET', 'POST'])
def change_username():
    if not session.get('authenticated'):
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        new_username = request.form['new_username']
        confirm_new_username = request.form['confirm_new_username']
        
        if new_username != confirm_new_username:
            flash('Usernames do not match. Please try again.', 'error')
            return redirect(url_for('account.change_username'))
        
        conn = get_db_connection()
        try:
            # Update the username
            conn.execute(
                'UPDATE users SET username = ? WHERE username = ?', 
                (new_username, session.get('username'))
            )
            conn.commit()
            
            # Update the session
            session['username'] = new_username
            
            flash('Username updated successfully!', 'success')
            return redirect(url_for('account.profile'))
        except sqlite3.IntegrityError:
            flash('This username is already in use. Please try a different one.', 'error')
        finally:
            conn.close()
    
    return render_template('account/change_username.html')