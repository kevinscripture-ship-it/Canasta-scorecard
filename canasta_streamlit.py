import streamlit as st
import requests
import pandas as pd
import time

# Page config
st.set_page_config(page_title="Canasta Scorekeeper", layout="wide", initial_sidebar_state="expanded")

# Firebase setup (test mode, no auth)
FIREBASE_URL = 'YOUR_FIREBASE_URL'  # Replace with your URL from Step 1 (e.g., https://canastascore-default-rtdb.firebaseio.com/)

# Sidebar
st.sidebar.header("Shared Game Setup")
game_id = st.sidebar.text_input("Game ID (e.g., game-101225)", key="game_id")
if st.sidebar.button("Create/Join Game"):
    st.session_state.game_id = game_id
    st.session_state.auto_refresh = st.sidebar.checkbox("Auto-refresh every 10s?", value=False)
    st.rerun()

# Team setup (4-player, 2 teams)
team1 = st.sidebar.text_input("Team 1 Name", value="Team 1")
team2 = st.sidebar.text_input("Team 2 Name", value="Team 2")
players = [
    st.sidebar.text_input("Player 1 (Team 1)", value="Player 1"),
    st.sidebar.text_input("Player 2 (Team 2)", value="Player 2"),
    st.sidebar.text_input("Player 3 (Team 1)", value="Player 3"),
    st.sidebar.text_input("Player 4 (Team 2)", value="Player 4")
]

game_target = 5000

# Helper functions for Firebase (no auth)
def get_firebase_data(path):
    try:
        response = requests.get(f"{FIREBASE_URL}{path}.json")
        return response.json() or {}
    except:
        return {}

def update_firebase_data(path, data):
    try:
        requests.put(f"{FIREBASE_URL}{path}.json", json=data)
    except:
        st.error("Error updating scores. Check internet or Game ID.")

# Main app
if 'game_id' in st.session_state:
    game_path = st.session_state.game_id.replace('/', '-')  # Sanitize for Firebase
    game_data = get_firebase_data(game_path)
    
    # Initialize or load data
    scores = game_data.get('scores', {team1: 0, team2: 0})
    dealer_index = game_data.get('dealer_index', 0)
    history = game_data.get('history', [])
    
    # Save setup
    update_firebase_data(game_path, {
        'scores': {team1: scores.get(team1, 0), team2: scores.get(team2, 0)},
        'dealer_index': dealer_index,
        'history': history,
        'players': players,
        'team_names': [team1, team2]
    })
    
    st.title("🃏 Shared Canasta Scorekeeper")
    st.info(f"🔗 Game ID: {game_id} | Share URL + ID with players. Refresh to see updates!")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Current Dealer", players[dealer_index])
        if st.button("🔄 Refresh Now"):
            st.cache_data.clear()
            st.rerun()
    with col2:
        st.metric(f"{team1} Score", scores[team1])
        st.metric(f"{team2} Score", scores[team2])
    
    # Auto-refresh (optional)
    if st.session_state.get('auto_refresh', False):
        time.sleep(10)
        st.rerun()
    
    with st.expander("🔄 New Round - Enter Details"):
        went_out = st.selectbox("Which team went out?", ['None', team1, team2])
        concealed = st.checkbox("Concealed hand? (+200 bonus)")
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader(team1)
            meld1 = st.number_input("Meld points", min_value=0, value=0, key="meld1")
            nat1 = st.slider("Natural Canastas", 0, 5, 0, key="nat1")
            mix1 = st.slider("Mixed Canastas", 0, 5, 0, key="mix1")
            red1 = st.slider("Red Threes", 0, 4, 0, key="red1")
        with col_b:
            st.subheader(team2)
            meld2 = st.number_input("Meld points", min_value=0, value=0, key="meld2")
            nat2 = st.slider("Natural Canastas", 0, 5, 0, key="nat2")
            mix2 = st.slider("Mixed Canastas", 0, 5, 0, key="mix2")
            red2 = st.slider("Red Threes", 0, 4, 0, key="red2")
        
        penalty1 = penalty2 = 0
        if went_out == team1:
            penalty2 = st.number_input(f"{team2} Penalty (hand cards)", min_value=0, value=0)
        elif went_out == team2:
            penalty1 = st.number_input(f"{team1} Penalty (hand cards)", min_value=0, value=0)
        else:
            penalty1 = st.number_input(f"{team1} Penalty (hand cards)", min_value=0, value=0)
            penalty2 = st.number_input(f"{team2} Penalty (hand cards)", min_value=0, value=0)
        
        if st.button("Tally Round!"):
            total_red = red1 + red2
            t1_can_bonus = (nat1 * 500) + (mix1 * 300)
            t2_can_bonus = (nat2 * 500) + (mix2 * 300)
            t1_red_bonus = red1 * 100 if total_red != 4 else (800 if red1 == 4 else 0)
            t2_red_bonus = red2 * 100 if total_red != 4 else (800 if red2 == 4 else 0)
            go_bonus = 200 if concealed else 100
            t1_go = go_bonus if went_out == team1 else 0
            t2_go = go_bonus if went_out == team2 else 0
            
            t1_round = meld1 + t1_can_bonus + t1_red_bonus + t1_go - penalty1
            t2_round = meld2 + t2_can_bonus + t2_red_bonus + t2_go - penalty2
            
            scores[team1] += t1_round
            scores[team2] += t2_round
            
            new_history = history + [{
                'Round': len(history) + 1,
                team1: t1_round,
                team2: t2_round,
                'Dealer': players[dealer_index]
            }]
            
            update_firebase_data(game_path, {
                'scores': scores,
                'history': new_history,
                'dealer_index': (dealer_index + 1) % 4,
                'players': players,
                'team_names': [team1, team2]
            })
            
            st.success("Scores updated! Tell others to refresh.")
            st.rerun()
    
    if history:
        st.subheader("📊 Shared Round History")
        df = pd.DataFrame(history)
        st.dataframe(df, use_container_width=True)
    
    if max(scores.values()) >= game_target:
        winner = team1 if scores[team1] >= scores[team2] else team2
        st.balloons()
        st.success(f"🎉 {winner} wins with {max(scores.values())} points!")
        if st.button("New Game"):
            update_firebase_data(game_path, {})
            st.rerun()

else:
    st.warning("Enter a Game ID in the sidebar and click Create/Join.")

# Rules
with st.expander("ℹ️ Quick Rules Reminder"):
    st.markdown("""
    - **Meld Points**: Jokers=50, A/2=20, K-8=10, 7-4=5.
    - **Canastas**: Natural=500, Mixed=300.
    - **Red 3s**: 100 each; 800 if all 4 to one team.
    - **Going Out**: +100 (or +200 concealed).
    - **Penalties**: Value of unmelded cards.
    Game ends at 5,000 points. Share Game ID to sync scores!
    """)
