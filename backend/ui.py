import streamlit as st
import requests
import json
import matplotlib.pyplot as plt
import numpy as np
import speech_recognition as sr
import pyttsx3
from gtts import gTTS
import os

st.set_page_config(page_title="CricketMind AI", layout="wide", initial_sidebar_state="collapsed")

# -------------------------------
# CUSTOM CSS
# -------------------------------
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        color: #1E88E5;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3rem;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover {
        border-color: #1E88E5;
        color: #1E88E5;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------
# INIT VOICE
# -------------------------------
recognizer = sr.Recognizer()
engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()

def play_frontend_audio(text):
    try:
        tts = gTTS(text=text, lang='en')
        tts.save("temp_audio.mp3")
        with open("temp_audio.mp3", "rb") as f:
            audio_bytes = f.read()
        st.audio(audio_bytes, format="audio/mp3", autoplay=True)
        os.remove("temp_audio.mp3")
    except Exception as e:
        st.error(f"Could not generate audio: {e}")

def listen():
    with sr.Microphone() as source:
        st.info("Listening... Speak now")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)

    try:
        text = recognizer.recognize_google(audio)
        st.success(f"You said: {text}")
        return text
    except:
        st.error("Could not understand voice")
        return ""

# -------------------------------
# LOAD DATA
# -------------------------------
with open("players.json") as f:
    players_list = list(json.load(f).keys())

# -------------------------------
# MATCHING
# -------------------------------
def match_player(name):
    name = name.lower()
    for player in players_list:
        if name in player.lower() or player.lower() in name:
            return player
    return None

def extract_players(text):
    text = text.lower()
    text = text.replace("versus", "vs")
    text = text.replace("and", "vs")
    text = text.replace("or", "vs")

    parts = text.split("vs")

    if len(parts) == 2:
        p1 = match_player(parts[0].strip())
        p2 = match_player(parts[1].strip())
        return p1, p2

    return None, None

# -------------------------------
# NORMALIZATION
# -------------------------------
def normalize_pair(v1, v2):
    max_vals = [max(a, b) for a, b in zip(v1, v2)]
    return (
        [a/m if m != 0 else 0 for a, m in zip(v1, max_vals)],
        [b/m if m != 0 else 0 for b, m in zip(v2, max_vals)]
    )

# -------------------------------
# RESULT FUNCTION
# -------------------------------
def show_results(data):

    st.subheader("Player Performance Breakdown")

    analysis = data["analysis"]
    players = list(analysis.keys())
    p1, p2 = players[0], players[1]

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"<h3 style='text-align: center; color: #4CAF50;'>{p1.replace('_',' ').title()}</h3>", unsafe_allow_html=True)
        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("Runs", analysis[p1].get("runs", 0))
        m2.metric("Average", analysis[p1].get("average", 0))
        m3.metric("Strike Rate", analysis[p1].get("strike_rate", 0))
        
        m4, m5, m6 = st.columns(3)
        m4.metric("Centuries", analysis[p1].get("centuries", "N/A"))
        m5.metric("Fifties", analysis[p1].get("fifties", "N/A"))
        m6.metric("Highest", analysis[p1].get("highest_score", "N/A"))

    with col2:
        st.markdown(f"<h3 style='text-align: center; color: #F44336;'>{p2.replace('_',' ').title()}</h3>", unsafe_allow_html=True)
        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("Runs", analysis[p2].get("runs", 0))
        m2.metric("Average", analysis[p2].get("average", 0))
        m3.metric("Strike Rate", analysis[p2].get("strike_rate", 0))
        
        m4, m5, m6 = st.columns(3)
        m4.metric("Centuries", analysis[p2].get("centuries", "N/A"))
        m5.metric("Fifties", analysis[p2].get("fifties", "N/A"))
        m6.metric("Highest", analysis[p2].get("highest_score", "N/A"))
        
    st.divider()

    # Radar chart
    st.subheader("Visual Performance Radar")

    labels = ["Runs", "Average", "Strike Rate"]

    p1_raw = [float(analysis[p1]["runs"]), float(analysis[p1]["average"]), float(analysis[p1]["strike_rate"])]
    p2_raw = [float(analysis[p2]["runs"]), float(analysis[p2]["average"]), float(analysis[p2]["strike_rate"])]

    p1_values, p2_values = normalize_pair(p1_raw, p2_raw)

    p1_values += p1_values[:1]
    p2_values += p2_values[:1]

    angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(subplot_kw=dict(polar=True))

    ax.plot(angles, p1_values, label=p1)
    ax.fill(angles, p1_values, alpha=0.25)

    ax.plot(angles, p2_values, label=p2)
    ax.fill(angles, p2_values, alpha=0.25)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)

    ax.legend()
    st.pyplot(fig)

    # Comparison
    st.subheader("Head-to-Head Insights")
    for point in data["comparison"]:
        st.write("•", point)

    # Commentary
    st.subheader("Expert AI Commentary")
    st.info(data["commentary"])
    
    text_to_speak = f"{data['commentary']} {data['verdict']}"
    play_frontend_audio(text_to_speak)

    # Verdict
    st.subheader("Final Verdict & Analysis")
    st.success(data["verdict"])

    # Prediction
    st.write("---")
    st.subheader("Match Outcome Prediction")

    winner = data["prediction"]
    confidence = data["confidence"]

    pred_col1, pred_col2 = st.columns([1, 2])
    
    with pred_col1:
        st.metric(label="Predicted Winner", value=winner.replace('_',' ').title())
        st.metric(label="Confidence Level", value=f"{confidence}%")
        
    with pred_col2:
        if winner.lower().replace(" ", "_") == p1.lower():
            st.success(f"🏏 {p1.replace('_',' ').title()} is predicted to win this matchup!")
        else:
            st.success(f"🏏 {p2.replace('_',' ').title()} is predicted to win this matchup!")
        
        try:
            st.progress(min(int(float(confidence)), 100))
        except:
            pass


# -------------------------------
# UI START
# -------------------------------
st.markdown("<h1 style='text-align: center; color: #1E88E5;'>🏏 CricketMind AI</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #555; font-size: 1.1rem;'>AI-powered cricket analytics comparing player performance, strengths, and match predictions.</p>", unsafe_allow_html=True)
st.write("---")

# -------------------------------
# SESSION STATE
# -------------------------------
if "player1" not in st.session_state:
    st.session_state.player1 = players_list[0]

if "player2" not in st.session_state:
    st.session_state.player2 = players_list[1]

# -------------------------------
# SELECT PLAYERS
# -------------------------------
col1, col2 = st.columns(2)
with col1:
    player1 = st.selectbox("Select Player 1", players_list, key="player1")
with col2:
    player2 = st.selectbox("Select Player 2", players_list, key="player2")

if player1 == player2:
    st.warning("Please select two different players")
    st.stop()

# -------------------------------
# ACTION BUTTONS
# -------------------------------
st.write("") # spacing
btn_col1, btn_col2, btn_col3 = st.columns([1, 2, 1])

action_clicked = False
with btn_col1:
    if st.button("🎤 Speak Players", key="voice_btn"):
        query = listen()
        if query:
            p1, p2 = extract_players(query)
            if p1 and p2:
                player1 = p1
                player2 = p2
                action_clicked = True
                st.success(f"Selected: {p1.replace('_',' ').title()} vs {p2.replace('_',' ').title()}")
            else:
                st.error("Could not detect two valid players from your voice.")
        
with btn_col3:
    if st.button("⚖️ Compare Players", type="primary", key="compare_btn"):
        action_clicked = True

# -------------------------------
# EXECUTE COMPARISON
# -------------------------------
if action_clicked:
    with st.spinner('Analyzing player data and generating expert commentary...'):
        response = requests.post(
            "http://127.0.0.1:8000/analyze",
            json={"player1": player1, "player2": player2}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "error":
                st.error(data["message"])
            else:
                st.write("---")
                show_results(data)
        else:
            st.error("Could not connect to the backend server. Is it running?")