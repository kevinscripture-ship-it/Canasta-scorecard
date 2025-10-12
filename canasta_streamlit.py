import streamlit as st

# Page config for PWA-like feel
st.set_page_config(page_title="Canasta Scorekeeper", layout="wide", initial_sidebar_state="expanded")

# Session state for persistence
if 'scores' not in st.session_state:
    st.session_state.scores = {'Team 1': 0, 'Team 2': 0}
if 'players' not in st.session_state:
    st.session_state.players = ['Player 1', 'Player 2', 'Player 3', 'Player 4']
if 'dealer_index' not in st.session_state:
    st.session_state.dealer_index = 0
if 'game_history' not in st.session_state:
    st.session_state.game_history = []
if 'team_names' not in st.session_state:
    st.session_state.team_names = ['Team 1', 'Team 2']

# Sidebar for setup
st.sidebar.header("Game Setup")
team1 = st.sidebar.text_input("Team 1 Name", value=st.session_state.team_names[0])
team2 = st.sidebar.text_input("Team 2 Name", value=st.session_state.team_names[1])
if st.sidebar.button("Update Teams"):
    st.session_state.team_names = [team1, team2]
    st.session_state.scores = {team1: 0, team2: 0}
    st.rerun()

for i in range(4):
    st.session_state.players[i] = st.sidebar.text_input(f"Player {i+1} Name", value=st.session_state.players[i])

game_target = 5000  # Standard Canasta win

# Main app
st.title("🃏 Canasta Scorekeeper")
st.markdown("Enter round details below to tally scores. Game ends at 5,000 points!")

col1, col2 = st.columns(2)
with col1:
    st.metric("Current Dealer", st.session_state.players[st.session_state.dealer_index])
with col2:
    st.metric(f"{st.session_state.team_names[0]} Score", st.session_state.scores[st.session_state.team_names[0]])
    st.metric(f"{st.session_state.team_names[1]} Score", st.session_state.scores[st.session_state.team_names[1]])

# Round inputs (use expanders for clean UI)
with st.expander("🔄 New Round - Enter Details", expanded=False):
    went_out = st.selectbox("Which team went out?", ['None', st.session_state.team_names[0], st.session_state.team_names[1]])
    concealed = st.checkbox("Concealed hand? (+200 bonus instead of +100)")
    
    # Team 1 inputs
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader(st.session_state.team_names[0])
        meld1 = st.number_input("Meld points", min_value=0, value=0, key="meld1")
        nat1 = st.slider("Natural Canastas", 0, 5, 0, key="nat1")
        mix1 = st.slider("Mixed Canastas", 0, 5, 0, key="mix1")
        red1 = st.slider("Red Threes", 0, 4, 0, key="red1")
    with col_b:
        st.subheader(st.session_state.team_names[1])
        meld2 = st.number_input("Meld points", min_value=0, value=0, key="meld2")
        nat2 = st.slider("Natural Canastas", 0, 5, 0, key="nat2")
        mix2 = st.slider("Mixed Canastas", 0, 5, 0, key="mix2")
        red2 = st.slider("Red Threes", 0, 4, 0, key="red2")
    
    # Penalties
    penalty1 = 0
    penalty2 = 0
    if went_out == st.session_state.team_names[0]:
        penalty2 = st.number_input(f"{st.session_state.team_names[1]} Penalty (hand cards)", min_value=0, value=0)
    elif went_out == st.session_state.team_names[1]:
        penalty1 = st.number_input(f"{st.session_state.team_names[0]} Penalty (hand cards)", min_value=0, value=0)
    else:
        penalty1 = st.number_input(f"{st.session_state.team_names[0]} Penalty (hand cards)", min_value=0, value=0)
        penalty2 = st.number_input(f"{st.session_state.team_names[1]} Penalty (hand cards)", min_value=0, value=0)
    
    if st.button("Tally Round!"):
        # Calculations (same logic as before)
        t1_can_bonus = (nat1 * 500) + (mix1 * 300)
        t2_can_bonus = (nat2 * 500) + (mix2 * 300)
        t1_red_bonus = red1 * 100
        t2_red_bonus = red2 * 100
        if red1 + red2 == 4:
            if red1 == 4: t1_red_bonus = 800
            elif red2 == 4: t2_red_bonus = 800
        go_bonus = 200 if concealed else 100
        t1_go = go_bonus if went_out == st.session_state.team_names[0] else 0
        t2_go = go_bonus if went_out == st.session_state.team_names[1] else 0
        
        t1_round = meld1 + t1_can_bonus + t1_red_bonus + t1_go - penalty1
        t2_round = meld2 + t2_can_bonus + t2_red_bonus + t2_go - penalty2
        
        st.session_state.scores[st.session_state.team_names[0]] += t1_round
        st.session_state.scores[st.session_state.team_names[1]] += t2_round
        
        # History
        round_entry = {
            'Round': len(st.session_state.game_history) + 1,
            st.session_state.team_names[0]: t1_round,
            st.session_state.team_names[1]: t2_round,
            'Dealer': st.session_state.players[st.session_state.dealer_index]
        }
        st.session_state.game_history.append(round_entry)
        
        # Rotate dealer
        st.session_state.dealer_index = (st.session_state.dealer_index + 1) % 4
        
        # Win check
        if max(st.session_state.scores.values()) >= game_target:
            winner = next(k for k, v in st.session_state.scores.items() if v >= game_target)
            st.success(f"🎉 {winner} wins with {st.session_state.scores[winner]} points!")
            if st.button("New Game"):
                for key in list(st.session_state.scores.keys()):
                    st.session_state.scores[key] = 0
                st.session_state.game_history = []
                st.session_state.dealer_index = 0
                st.rerun()
        
        st.rerun()

# Display history table
if st.session_state.game_history:
    st.subheader("📊 Round History")
    import pandas as pd
    df = pd.DataFrame(st.session_state.game_history)
    st.dataframe(df, use_container_width=True)

# Instructions
with st.expander("ℹ️ Quick Rules Reminder"):
    st.markdown("""
    - **Meld Points**: Sum of cards in melds (Jokers=50, A/2=20, K-8=10, 7-4=5).
    - **Canastas**: Natural (500 pts), Mixed (300 pts).
    - **Red 3s**: 100 each; 800 if all 4 to one team.
    - **Going Out**: +100 (or +200 concealed).
    - Penalties: Value of unmelded cards if not out.
    """)
