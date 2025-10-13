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
        st.error(f"Error updating Firebase: {str(e)}")

# Calculate required meld
def get_required_meld(score):
    if score < 1500:
        return 50
    elif score < 3000:
        return 90
    else:
        return 120

# Render table graphic with players and highlighted dealer
def render_table(players, dealer_index):
    table_image_url = "https://www.wikihow.com/images/thumb/b/b2/Play-Canasta-Step-16-Version-2.jpg/v4-460px-Play-Canasta-Step-16-Version-2.jpg"
    html = f"""
    <div style="position: relative; width: 100%; max-width: 460px; margin: auto;">
        <img src="{table_image_url}" style="width: 100%; height: auto;">
        <div style="position: absolute; bottom: 0; left: 50%; transform: translate(-50%, -10%); color: {'red' if dealer_index == 0 else 'black'}; font-weight: {'bold' if dealer_index == 0 else 'normal'};">
            {players[0]} (South) {'⭐' if dealer_index == 0 else ''}
        </div>
        <div style="position: absolute; left: 0; top: 50%; transform: translate(-10%, -50%); color: {'red' if dealer_index == 1 else 'black'}; font-weight: {'bold' if dealer_index == 1 else 'normal'};">
            {players[1]} (West) {'⭐' if dealer_index == 1 else ''}
        </div>
        <div style="position: absolute; top: 0; left: 50%; transform: translate(-50%, -10%); color: {'red' if dealer_index == 2 else 'black'}; font-weight: {'bold' if dealer_index == 2 else 'normal'};">
            {players[2]} (North) {'⭐' if dealer_index == 2 else ''}
        </div>
        <div style="position: absolute; right: 0; top: 50%; transform: translate(10%, -50%); color: {'red' if dealer_index == 3 else 'black'}; font-weight: {'bold' if dealer_index == 3 else 'normal'};">
            {players[3]} (East) {'⭐' if dealer_index == 3 else ''}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# Main logic
if st.session_state.game_id is None:
    st.session_state.view = 'setup'  # Force setup if no game ID

if st.session_state.view == 'setup':
    st.header("Game Setup")
    render_table(st.session_state.players, 0)  # Preview with Player 1 as example dealer
    col1, col2 = st.columns([1, 1])
    with col1:
        st.session_state.team1 = st.text_input("Team 1 Name", value=st.session_state.team1)
        st.session_state.players[0] = st.text_input("Player 1 (Team 1, South)", value=st.session_state.players[0])
        st.session_state.players[2] = st.text_input("Player 3 (Team 1, North)", value=st.session_state.players[2])
    with col2:
        st.session_state.team2 = st.text_input("Team 2 Name", value=st.session_state.team2)
        st.session_state.players[1] = st.text_input("Player 2 (Team 2, West)", value=st.session_state.players[1])
        st.session_state.players[3] = st.text_input("Player 4 (Team 2, East)", value=st.session_state.players[3])
    
    game_id_input = st.text_input("Game ID (e.g., game-101225)")
    if st.button("Start Game", use_container_width=True):
        if game_id_input:
            st.session_state.game_id = game_id_input
            st.session_state.view = 'summary'
            st.rerun()

else:
    game_path = st.session_state.game_id.replace('/', '-')  # Sanitize
    game_data = get_firebase_data(game_path)
    
    # Load data
    scores = game_data.get('scores', {st.session_state.team1: 0, st.session_state.team2: 0})
    dealer_index = game_data.get('dealer_index', 0)
    history = game_data.get('history', [])
    
    # Save setup
    update_firebase_data(game_path, {
        'scores': {st.session_state.team1: scores.get(st.session_state.team1, 0), st.session_state.team2: scores.get(st.session_state.team2, 0)},
        'dealer_index': dealer_index,
        'history': history,
        'players': st.session_state.players,
        'team_names': [st.session_state.team1, st.session_state.team2]
    })
    
    # Sidebar for options
    st.sidebar.header("Options")
    st.session_state.auto_refresh = st.sidebar.checkbox("Auto-refresh every 10s?", value=st.session_state.auto_refresh)
    if st.sidebar.button("Edit Setup"):
        st.session_state.view = 'setup'
        st.rerun()
    
    if st.session_state.view == 'summary':
        st.header("Game Summary")
        render_table(st.session_state.players, dealer_index)
        
        # Scores and required meld
        col_score1, col_score2 = st.columns(2)
        with col_score1:
            st.metric(f"{st.session_state.team1} Score", scores.get(st.session_state.team1, 0))
