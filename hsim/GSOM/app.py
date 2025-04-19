import streamlit as st
import pandas as pd
from hsim.GSOM.backend import runner

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

# Step 1: Enter username
user_name = st.text_input("Enter your username and press Enter:")
if not user_name:
    st.stop()

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
        processed_data, output = runner(uploaded_file, user_name)
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



