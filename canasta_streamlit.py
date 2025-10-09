import streamlit as st
import pandas as pd

# Page config
st.set_page_config(page_title="Canasta Scorekeeper", layout="wide", initial_sidebar_state="expanded")

# Session state for persistence
if 'num_players' not in st.session_state:
    st.session_state.num_players = 4  # Default
if 'scores' not in st.session_state:
    st.session_state.scores = {}
if 'players' not in st.session_state:
    st.session_state.players = []
if 'dealer_index' not in st.session_state:
    st.session_state.dealer_index = 0
if 'game_history' not in st.session_state:
    st.session_state.game_history = []
if 'side_names' not in st.session_state:
    st.session_state.side_names = []

# Sidebar for setup
st.sidebar.header("Game Setup")
num_players = st.sidebar.selectbox("Number of Players", [2, 4, 6], index=1)  # Dropdown here!

if num_players != st.session_state.num_players:
    # Reset on change
    st.session_state.num_players = num_players
    st.session_state.scores = {}
    st.session_state.players = []
    st.session_state.side_names = []
    st.session_state.game_history = []
    st.session_state.dealer_index = 0
    st.rerun()

# Determine num_sides and type
if num_players == 2:
    num_sides = 2
    side_type = "Individuals"
elif num_players == 4:
    num_sides = 2
    side_type = "Teams"
elif num_players == 6:
    num_sides = 3
    side_type = "Teams"

# Side names (e.g., Team/Individual names)
st.sidebar.subheader(f"{side_type} Names")
for i in range(num_sides):
    default_name = f"{side_type} {i+1}"
    side_name = st.sidebar.text_input(f"{side_type} {i+1} Name", value=default_name, key=f"side_{i}")
    if side_name != st.session_state.side_names[i] if i < len(st.session_state.side_names) else True:
        st.session_state.side_names = [side_name] * num_sides  # Simplified; update all if needed
        st.session_state.scores = {side_name: 0 for side_name in st.session_state.side_names}

# Player names for dealer
st.sidebar.subheader("Player Names (for Dealer Rotation)")
for i in range(num_players):
    default_player = f"Player {i+1}"
    player_name = st.sidebar.text_input(f"Player {i+1}", value=default_player, key=f"player_{i}")

if st.sidebar.button("Start/Update Game"):
    st.session_state.players = [st.sidebar.text_input(f"Player {j+1}", value=st.session_state.players[j] if j < len(st.session_state.players) else f"Player {j+1}", key=f"player_{j}") for j in range(num_players)]
    st.session_state.side_names = [st.sidebar.text_input(f"{side_type} {k+1} Name", value=st.session_state.side_names[k] if k < len(st.session_state.side_names) else f"{side_type} {k+1}", key=f"side_{k}") for k in range(num_sides)]
    st.session_state.scores = {name: 0 for name in st.session_state.side_names}
    st.rerun()

game_target = 5000  # Standard for all variants

# Main app (only if setup done)
if st.session_state.side_names and st.session_state.players:
    st.title(f"🃏 {num_players}-Player Canasta Scorekeeper ({side_type})")
    st.info(f"Live scores for {', '.join(st.session_state.side_names)}. Game ends when any reaches {game_target} points!")

    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric("Current Dealer", st.session_state.players[st.session_state.dealer_index])
    with col2:
        score_cols = st.columns(num_sides)
        for i, side in enumerate(st.session_state.side_names):
            with score_cols[i]:
                st.metric(side, st.session_state.scores[side])

    # Round inputs
    with st.expander("🔄 New Round - Enter Details", expanded=False):
        went_out_options = ['None'] + st.session_state.side_names
        went_out = st.selectbox("Which side went out?", went_out_options)
        concealed = st.checkbox("Concealed hand? (+200 bonus instead of +100)")

        # Dynamic inputs for each side
        input_cols = st.columns(num_sides)
        side_inputs = {}
        for i, side in enumerate(st.session_state.side_names):
            with input_cols[i]:
                st.subheader(side)
                side_inputs[side] = {
                    'meld': st.number_input("Meld points", min_value=0, value=0, key=f"meld_{side}"),
                    'nat': st.slider("Natural Canastas", 0, 5, 0, key=f"nat_{side}"),
                    'mix': st.slider("Mixed Canastas", 0, 5, 0, key=f"mix_{side}"),
                    'red': st.slider("Red Threes", 0, 4, 0, key=f"red_{side}")
                }

        # Penalties (only for non-out sides)
        penalty_inputs = {}
        if went_out != 'None':
            for side in st.session_state.side_names:
                if side != went_out:
                    penalty = st.number_input(f"{side} Penalty (hand cards)", min_value=0, value=0, key=f"penalty_{side}")
                    penalty_inputs[side] = penalty
        else:
            # All penalized if no one out
            for side in st.session_state.side_names:
                penalty = st.number_input(f"{side} Penalty (hand cards)", min_value=0, value=0, key=f"penalty_{side}")
                penalty_inputs[side] = penalty

        if st.button("Tally Round!"):
            # Calculate for each side
            round_scores = {}
            total_red = sum(side_inputs[side]['red'] for side in st.session_state.side_names)
            for side in st.session_state.side_names:
                inputs = side_inputs[side]
                can_bonus = (inputs['nat'] * 500) + (inputs['mix'] * 300)
                red_bonus = inputs['red'] * 100
                if total_red == 4:
                    if inputs['red'] == 4:
                        red_bonus = 800
                go_bonus = 0
                if went_out == side:
                    go_bonus = 200 if concealed else 100
                penalty = penalty_inputs.get(side, 0)
                round_score = inputs['meld'] + can_bonus + red_bonus + go_bonus - penalty
                round_scores[side] = round_score
                st.session_state.scores[side] += round_score

            # History
            round_entry = {side: round_scores[side] for side in st.session_state.side_names}
            round_entry['Round'] = len(st.session_state.game_history) + 1
            round_entry['Dealer'] = st.session_state.players[st.session_state.dealer_index]
            st.session_state.game_history.append(round_entry)

            # Rotate dealer
            st.session_state.dealer_index = (st.session_state.dealer_index + 1) % num_players

            # Win check
            max_score = max(st.session_state.scores.values())
            if max_score >= game_target:
                winner = next(side for side, score in st.session_state.scores.items() if score == max_score)
                st.success(f"🎉 {winner} wins with {max_score} points!")
                if st.button("New Game"):
                    st.session_state.scores = {side: 0 for side in st.session_state.side_names}
                    st.session_state.game_history = []
                    st.session_state.dealer_index = 0
                    st.rerun()

            st.rerun()

    # History table
    if st.session_state.game_history:
        st.subheader("📊 Round History")
        df = pd.DataFrame(st.session_state.game_history)
        st.dataframe(df, use_container_width=True)

    # Instructions with variant notes
    with st.expander("ℹ️ Quick Rules Reminder"):
        st.markdown("""
        **Core Scoring (All Variants)**: Meld Points (Jokers=50, A/2=20, K-8=10, 7-4=5). Natural Canasta=500, Mixed=300. Red 3s=100 each (800 if all 4 to one side). Going Out=+100 (+200 concealed). Penalties=Value of unmelded cards.
        
        **Variant Notes**:
        - **2-Player**: Individuals; need *2 canastas* to go out. Dealt 15 cards, draw 1.
        - **4-Player**: 2 teams; need 1 canasta to go out. Dealt 11 cards, draw 1.
        - **6-Player**: 3 teams of 2; need 1 canasta to go out. Dealt 11-13 cards, draw 1.
        
        Win: First side to 5,000. Input your canasta counts accurately for going out eligibility!
        """)

else:
    st.warning("Set up teams/individuals and players in the sidebar, then click Start/Update Game.")
