import streamlit as st
import pandas as pd
import sqlite3
import re
import smtplib
from email.mime.text import MIMEText
from hsim.GSOM.backend import runner
from concurrent.futures import ThreadPoolExecutor


# Initialize SQLite database for user authentication
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

# Streamlit app title
st.title("Simulation and Results Processor")

# Initialize session state
if "processed_data" not in st.session_state:
    st.session_state.processed_data = None
if "download_data" not in st.session_state:
    st.session_state.download_data = None
if "run_simulation" not in st.session_state:
    st.session_state.run_simulation = False
if "last_uploaded_file" not in st.session_state:
    st.session_state.last_uploaded_file = None
if "simulation_success" not in st.session_state:
    st.session_state.simulation_success = False
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None

# Function to send email
def send_reset_email(email, username, new_password):
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
        st.error(f"Failed to send email: {e}")
        return False

# Sidebar for login/register/forgot password
with st.sidebar:
    st.header("User Authentication")
    if not st.session_state.authenticated:
        auth_choice = st.radio("Choose an option:", ["Login", "Register", "Forgot Password"])

        if auth_choice == "Register":
            new_username = st.text_input("Enter a new username:")
            new_email = st.text_input("Enter your email:")
            new_password = st.text_input("Enter a new password:", type="password")
            confirm_password = st.text_input("Confirm your password:", type="password")

            # Email validation with regex
            email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
            if st.button("Register"):
                if not re.match(email_regex, new_email):
                    st.error("Invalid email format. Please enter a valid email.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match. Please try again.")
                else:
                    try:
                        cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                                       (new_username, new_email, new_password))
                        conn.commit()
                        st.success("Registration successful! Please log in.")
                        st.rerun()  # Refresh the sidebar
                    except sqlite3.IntegrityError:
                        st.error("Username or email already exists. Please try again.")
        elif auth_choice == "Login":
            username = st.text_input("Username:")
            password = st.text_input("Password:", type="password")
            if st.button("Login"):
                cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
                user = cursor.fetchone()
                if user:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.success("Login successful!")
                    st.rerun()  # Refresh the sidebar
                else:
                    st.error("Invalid username or password.")
        elif auth_choice == "Forgot Password":
            identifier = st.text_input("Enter your username or email:")
            if st.button("Reset Password"):
                cursor.execute("SELECT username, email FROM users WHERE username = ? OR email = ?", (identifier, identifier))
                user = cursor.fetchone()
                if user:
                    username, email = user
                    new_password = "newpassword123"  # Generate a secure random password in production
                    cursor.execute("UPDATE users SET password = ? WHERE username = ?", (new_password, username))
                    conn.commit()
                    if send_reset_email(email, username, new_password):
                        st.success("A reset email has been sent to your email address.")
                else:
                    st.error("No account found with the provided username or email.")
    else:
        st.write(f"Logged in as: {st.session_state.username}")

        # Options for account management
        account_action = st.radio("Account Management:", ["None", "Change Password", "Change Email", "Change Username"])

        if account_action == "Change Password":
            st.subheader("Change Password")
            old_password = st.text_input("Enter your old password:", type="password")
            new_password = st.text_input("Enter a new password:", type="password")
            confirm_new_password = st.text_input("Confirm your new password:", type="password")
            if st.button("Update Password"):
                if new_password != confirm_new_password:
                    st.error("New passwords do not match. Please try again.")
                else:
                    cursor.execute("SELECT password FROM users WHERE username = ?", (st.session_state.username,))
                    current_password = cursor.fetchone()
                    if current_password and current_password[0] == old_password:
                        cursor.execute("UPDATE users SET password = ? WHERE username = ?", (new_password, st.session_state.username))
                        conn.commit()
                        st.success("Password updated successfully!")
                    else:
                        st.error("Old password is incorrect. Please try again.")

        elif account_action == "Change Email":
            st.subheader("Change Email")
            new_email = st.text_input("Enter your new email:")
            confirm_new_email = st.text_input("Confirm your new email:")
            if st.button("Update Email"):
                email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
                if new_email != confirm_new_email:
                    st.error("Emails do not match. Please try again.")
                elif not re.match(email_regex, new_email):
                    st.error("Invalid email format. Please enter a valid email.")
                else:
                    try:
                        cursor.execute("UPDATE users SET email = ? WHERE username = ?", (new_email, st.session_state.username))
                        conn.commit()
                        st.success("Email updated successfully!")
                    except sqlite3.IntegrityError:
                        st.error("This email is already in use. Please try a different one.")

        elif account_action == "Change Username":
            st.subheader("Change Username")
            new_username = st.text_input("Enter your new username:")
            confirm_new_username = st.text_input("Confirm your new username:")
            if st.button("Update Username"):
                if new_username != confirm_new_username:
                    st.error("Usernames do not match. Please try again.")
                else:
                    try:
                        cursor.execute("UPDATE users SET username = ? WHERE username = ?", (new_username, st.session_state.username))
                        conn.commit()
                        st.session_state.username = new_username  # Update session state
                        st.success("Username updated successfully!")
                        st.rerun()  # Refresh the sidebar
                    except sqlite3.IntegrityError:
                        st.error("This username is already in use. Please try a different one.")

        # Logout Button
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.rerun()  # Refresh the sidebar

# Main app content
if not st.session_state.authenticated:
    st.stop()

# Step 1: Enter username
user_name = st.session_state.username
st.write(f"Welcome, {user_name}!")

# Step 2: File upload section
uploaded_file = st.file_uploader("Upload your simulation file (.xlsx only)", type=["xlsx"])

# Step 5: Reset session state on new file upload
if uploaded_file is not None:
    if st.session_state.last_uploaded_file != uploaded_file.name:
        st.session_state.processed_data = None
        st.session_state.download_data = None
        st.session_state.run_simulation = False
        st.session_state.simulation_success = False
        st.session_state.last_uploaded_file = uploaded_file.name

# Step 3: Enable "Run" button
col1, col2 = st.columns([1, 3])
with col1:
    if uploaded_file is not None:
        if st.button("Run Simulation"):
            st.session_state.run_simulation = True

with col2:
    if st.session_state.simulation_success:
        st.success("Simulation completed successfully!")

# Step 4 & 6: Process file and generate results
if uploaded_file is not None and st.session_state.run_simulation:
    try:
        # Call runner function to process the file
        with st.spinner("Processing in background..."):
        # Create a ThreadPoolExecutor
            with ThreadPoolExecutor() as executor:
                # Submit the task
                future = executor.submit(runner, uploaded_file, user_name)
                
                # You can do other things here while waiting
                
                # Get the result when ready
                processed_data, output = future.result()
        # processed_data, output = runner(uploaded_file, user_name)
        st.session_state.processed_data = processed_data
        st.session_state.download_data = output.getvalue()

        st.session_state.simulation_success = True
        st.session_state.run_simulation = False  # Allow re-running the same file

    except Exception as e:
        st.error(f"An error occurred: {e}")

# Step 7: Display download button if results are available
if st.session_state.download_data is not None:
    st.download_button(
        label="Download Results",
        data=st.session_state.download_data,
        file_name="simulation_results.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Periodically render a table with data from results.csv
st.markdown("---")
st.subheader("Leaderboard")

try:
    results_df = pd.read_csv("results.csv",header=0)
    st.dataframe(results_df)
except FileNotFoundError:
    st.info("No results available yet. Run a simulation to generate results.")



