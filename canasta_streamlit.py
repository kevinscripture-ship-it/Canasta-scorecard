import streamlit as st
import requests
import pandas as pd
import time
import base64  # For embedding images if needed

# Page config for mobile-friendliness
st.set_page_config(page_title="Canasta Scorekeeper", layout="wide", initial_sidebar_state="collapsed")

# Firebase setup (test mode, no auth)
FIREBASE_URL = 'https://canastakeeper-b0cf4-default-rtdb.firebaseio.com/'  # Your Firebase URL

# Global game target
game_target = 5000

# Initialize session state
if 'view' not in st.session_state:
    st.session_state.view = 'setup'  # Start with setup
if 'game_id' not in st.session_state:
    st.session_state.game_id = None
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False
if 'team1' not in st.session_state:
    st.session_state.team1 = "Team 1"
if 'team2' not in st.session_state:
    st.session_state.team2 = "Team 2"
if 'players' not in st.session_state:
    st.session_state.players = ["Player 1", "Player 2", "Player 3", "Player 4"]

# Firebase helpers
def get_firebase_data(path):
    try:
        response = requests.get(f"{FIREBASE_URL}{path}.json")
        if response.status_code == 200:
            return response.json() or {}
        else:
            st.error("Failed to fetch data from Firebase. Check internet or Game ID.")
            return {}
    except Exception as e:
        st.error(f"Error connecting to Firebase: {str(e)}")
        return {}

def update_firebase_data(path, data):
    try:
        response = requests.put(f"{FIREBASE_URL}{path}.json", json=data)
        if response.status_code != 200:
            st.error("Failed to update Firebase. Check internet or Game ID.")
    except Exception as e:
        st.error(f"Error updating Firebase:
