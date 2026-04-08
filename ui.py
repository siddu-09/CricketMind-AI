from io import BytesIO
import os
import re

from gtts import gTTS
import matplotlib.pyplot as plt
import numpy as np
import requests
import speech_recognition as sr
import streamlit as st


BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000/analyze")
LANGUAGE_OPTIONS = {
  "English": "en",
  "Hindi": "hi",
  "Kannada": "kn",
}
COMMON_PLAYER_ALIASES = {
    "kohli": "Virat Kohli",
    "virat": "Virat Kohli",
  "king": "Virat Kohli",
  "king kohli": "Virat Kohli",
  "chase master": "Virat Kohli",
    "sharma": "Rohit Sharma",
    "rohit": "Rohit Sharma",
  "hitman": "Rohit Sharma",
  "the hitman": "Rohit Sharma",
    "dhoni": "MS Dhoni",
    "msd": "MS Dhoni",
  "thala": "MS Dhoni",
  "captain cool": "MS Dhoni",
    "rahul": "KL Rahul",
    "hardik": "Hardik Pandya",
    "bumrah": "Jasprit Bumrah",
  "boom": "Jasprit Bumrah",
  "boom boom": "Jasprit Bumrah",
    "siraj": "Mohammed Siraj",
    "sachin": "Sachin Tendulkar",
  "master blaster": "Sachin Tendulkar",
}
recognizer = sr.Recognizer()


st.set_page_config(
    page_title="CricketMind AI",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

:root {
  --ink: #132a13;
  --card: #f8f4e8;
  --surface: #fffdf7;
  --accent: #ff7a00;
  --accent-2: #1b4332;
  --muted: #5f6f52;
}

html, body, [class*="css"] {
  font-family: 'IBM Plex Sans', sans-serif;
}

.stApp {
  background:
    radial-gradient(circle at 10% 10%, #ffe9c8 0%, transparent 30%),
    radial-gradient(circle at 90% 30%, #d8f3dc 0%, transparent 35%),
    linear-gradient(145deg, #fffef8 0%, #f5f7f1 60%, #fff8ed 100%);
}

/* Global readability on light theme */
.stApp,
.stApp p,
.stApp span,
.stApp li,
.stApp label,
.stMarkdown,
.stMarkdown p,
.stMarkdown li,
div[data-testid="stText"],
div[data-testid="stMarkdownContainer"] {
  color: var(--ink) !important;
}

h1, h2, h3 {
  font-family: 'Space Grotesk', sans-serif;
  letter-spacing: -0.02em;
  color: var(--ink);
}

.hero {
  background: linear-gradient(120deg, #1b4332 0%, #2d6a4f 65%, #40916c 100%);
  border-radius: 18px;
  color: white;
  padding: 24px;
  margin-bottom: 12px;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.12);
}

.hero p {
  margin-bottom: 0;
  opacity: 0.92;
}

.hero h1,
.hero p {
  color: #ffffff !important;
}

.metric-card {
  background: var(--card);
  border-left: 6px solid var(--accent);
  border-radius: 14px;
  padding: 12px 14px;
  margin: 8px 0;
}

.metric-title {
  color: var(--muted);
  font-size: 0.85rem;
}

.metric-value {
  font-family: 'Space Grotesk', sans-serif;
  color: var(--ink);
  font-size: 1.25rem;
  font-weight: 700;
}

.tag {
  display: inline-block;
  border-radius: 999px;
  padding: 4px 10px;
  background: #ffe8d6;
  color: #7f4f24;
  font-size: 0.78rem;
  margin-top: 6px;
}

div[data-testid="stMetricValue"] {
  color: var(--ink);
}

div[data-testid="stMetricLabel"] {
  color: var(--muted) !important;
}

/* Form controls */
div[data-baseweb="input"] input {
  color: var(--ink) !important;
  background-color: #fffef9 !important;
}

div[data-baseweb="input"] input::placeholder {
  color: #6b705c !important;
  opacity: 1 !important;
}

/* Alert readability */
div[data-testid="stAlert"] p,
div[data-testid="stAlert"] span {
  color: #132a13 !important;
}

.stButton > button {
  width: 100%;
  height: 3rem;
  border-radius: 12px;
  border: 1px solid #1b4332;
  font-weight: 600;
}

.stButton > button:hover {
  border-color: var(--accent);
  color: var(--accent);
}

#MainMenu, footer, header {
  visibility: hidden;
}
</style>
""",
    unsafe_allow_html=True,
)


def to_float(value):
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return 0.0


def normalize_pair(values1, values2):
    max_vals = [max(a, b) for a, b in zip(values1, values2)]
    return (
        [a / m if m else 0 for a, m in zip(values1, max_vals)],
        [b / m if m else 0 for b, m in zip(values2, max_vals)],
    )


def player_block(title, stats, format_used):
    st.markdown(f"### {title}")
    st.markdown(
        f"""
        <div class="metric-card">
          <div class="metric-title">Runs</div>
          <div class="metric-value">{stats.get('runs', 'N/A')}</div>
        </div>
        <div class="metric-card">
          <div class="metric-title">Average</div>
          <div class="metric-value">{stats.get('average', 'N/A')}</div>
        </div>
        <div class="metric-card">
          <div class="metric-title">Strike Rate</div>
          <div class="metric-value">{stats.get('strike_rate', 'N/A')}</div>
        </div>
        <span class="tag">Stats Basis: {format_used.upper()}</span>
        """,
        unsafe_allow_html=True,
    )


def draw_radar(name1, name2, stats1, stats2):
    labels = ["Runs", "Average", "Strike Rate"]
    raw1 = [to_float(stats1.get("runs")), to_float(stats1.get("average")), to_float(stats1.get("strike_rate"))]
    raw2 = [to_float(stats2.get("runs")), to_float(stats2.get("average")), to_float(stats2.get("strike_rate"))]
    v1, v2 = normalize_pair(raw1, raw2)

    v1 += v1[:1]
    v2 += v2[:1]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(4.2, 4.2), subplot_kw={"polar": True})
    ax.set_facecolor("#fffdf7")
    ax.plot(angles, v1, linewidth=2.2, label=name1, color="#ff7a00")
    ax.fill(angles, v1, alpha=0.22, color="#ff7a00")
    ax.plot(angles, v2, linewidth=2.2, label=name2, color="#1b4332")
    ax.fill(angles, v2, alpha=0.22, color="#1b4332")
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.set_yticklabels([])
    ax.grid(alpha=0.25)
    ax.legend(loc="upper right", bbox_to_anchor=(1.2, 1.1))
    st.pyplot(fig, use_container_width=False)


def extract_players_from_text(text):
    if not text:
        return None, None

    normalized = str(text).lower().strip()
    normalized = re.sub(r"\s+", " ", normalized)
    parts = [p.strip(" ,.-") for p in re.split(r"\b(?:versus|vs|v|and)\b", normalized) if p.strip(" ,.-")]

    if len(parts) >= 2:
        return parts[0].title(), parts[1].title()

    comma_parts = [p.strip(" ,.-") for p in normalized.split(",") if p.strip(" ,.-")]
    if len(comma_parts) >= 2:
        return comma_parts[0].title(), comma_parts[1].title()

    return None, None


def resolve_player_alias(name):
    clean_name = str(name or "").strip().lower()
    if not clean_name:
        return ""

    normalized = re.sub(r"[^a-z0-9\s]", " ", clean_name)
    normalized = re.sub(r"\s+", " ", normalized).strip()

    if normalized in COMMON_PLAYER_ALIASES:
        return COMMON_PLAYER_ALIASES[normalized]
    if clean_name in COMMON_PLAYER_ALIASES:
        return COMMON_PLAYER_ALIASES[clean_name]

    tokens = normalized.split()
    for i in range(len(tokens)):
        for j in range(i + 1, len(tokens) + 1):
            phrase = " ".join(tokens[i:j])
            if phrase in COMMON_PLAYER_ALIASES:
                return COMMON_PLAYER_ALIASES[phrase]

    return str(name).strip().title()


def transcribe_speech(audio_file):
    if audio_file is None:
        return ""

    audio_bytes = audio_file.getvalue()
    if not audio_bytes:
        return ""

    with sr.AudioFile(BytesIO(audio_bytes)) as source:
        audio_data = recognizer.record(source)

    try:
        return recognizer.recognize_google(audio_data)
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as exc:
        raise RuntimeError(f"Speech recognition service error: {exc}") from exc


@st.cache_data(show_spinner=False)
def generate_tts_audio(text, language_code):
    clean_text = (text or "").strip()
    if not clean_text:
        return b""

    audio_fp = BytesIO()
    tts = gTTS(text=clean_text, lang=language_code, slow=False)
    tts.write_to_fp(audio_fp)
    audio_fp.seek(0)
    return audio_fp.read()


def call_backend(player1, player2, language):
    return requests.post(
        BACKEND_URL,
    json={
      "player1": player1.strip(),
      "player2": player2.strip(),
      "language": language,
    },
        timeout=60,
    )


st.markdown(
    """
    <section class="hero">
      <h1>CricketMind AI</h1>
      <p>Live player-vs-player analytics powered by CricketData API + LLM commentary.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

if "player1" not in st.session_state:
    st.session_state.player1 = "Virat Kohli"
if "player2" not in st.session_state:
    st.session_state.player2 = "Rohit Sharma"

# Apply speech-derived updates before rendering text_input widgets.
if "pending_player1" in st.session_state and "pending_player2" in st.session_state:
  st.session_state.player1 = st.session_state.pop("pending_player1")
  st.session_state.player2 = st.session_state.pop("pending_player2")

input_col1, input_col2 = st.columns(2)
with input_col1:
    player1 = st.text_input("Player 1", key="player1", placeholder="e.g. Virat Kohli")
with input_col2:
    player2 = st.text_input("Player 2", key="player2", placeholder="e.g. Rohit Sharma")

input_mode = st.radio(
  "Player input mode",
  options=["Text", "Speech"],
  horizontal=True,
)

if input_mode == "Speech":
  st.caption("Record and say both players, for example: Virat Kohli versus Rohit Sharma")
  speech_audio = st.audio_input("Speak player names")
  speech_apply = st.button("Use Speech Input")

  if speech_apply:
    if speech_audio is None:
      st.warning("Please record your voice first.")
    else:
      with st.spinner("Transcribing speech..."):
        try:
          transcript = transcribe_speech(speech_audio)
        except RuntimeError as exc:
          st.error(str(exc))
          transcript = ""

      if transcript:
        st.success(f"Heard: {transcript}")
        spoken_p1, spoken_p2 = extract_players_from_text(transcript)
        if spoken_p1 and spoken_p2:
          st.session_state.pending_player1 = resolve_player_alias(spoken_p1)
          st.session_state.pending_player2 = resolve_player_alias(spoken_p2)
          st.rerun()
        else:
          st.warning("Could not detect two player names. Try saying: Player one versus player two.")
      else:
        st.warning("Could not understand audio. Please try again clearly.")

language_label = st.selectbox(
  "Commentary language",
  options=list(LANGUAGE_OPTIONS.keys()),
  index=0,
)
selected_language = LANGUAGE_OPTIONS[language_label]

compare_clicked = st.button("Compare Players", type="primary")

if compare_clicked:
  player1_resolved = resolve_player_alias(player1)
  player2_resolved = resolve_player_alias(player2)

  if not player1_resolved.strip() or not player2_resolved.strip():
    st.error("Please enter both player names.")
  elif player1_resolved.strip().lower() == player2_resolved.strip().lower():
    st.warning("Please enter two different players.")
  else:
    if player1_resolved != player1 or player2_resolved != player2:
      st.caption(f"Interpreting input as: {player1_resolved} vs {player2_resolved}")

    with st.spinner("Fetching live stats and generating analysis..."):
      try:
        response = call_backend(player1_resolved, player2_resolved, selected_language)
      except requests.RequestException as exc:
        st.error(f"Could not reach backend at {BACKEND_URL}: {exc}")
        st.stop()

      if response.status_code != 200:
        st.error(f"Backend request failed with status code {response.status_code}.")
        st.stop()

      result = response.json()
      if result.get("status") == "error":
        st.error(result.get("message", "Unknown API error."))
        st.stop()

      analysis = result.get("analysis", {})
      keys = list(analysis.keys())
      if len(keys) < 2:
        st.error("Unexpected response format: analysis data missing.")
        st.stop()

      k1, k2 = keys[0], keys[1]
      stats1, stats2 = analysis[k1], analysis[k2]
      formats = result.get("format_used", {})

      st.write("")
      c1, c2 = st.columns(2)
      with c1:
        player_block(player1_resolved.title(), stats1, formats.get("player1", "unknown"))
      with c2:
        player_block(player2_resolved.title(), stats2, formats.get("player2", "unknown"))

      st.subheader("Performance Radar")
      draw_radar(player1_resolved.title(), player2_resolved.title(), stats1, stats2)

      st.subheader("Head-to-Head Insights")
      for item in result.get("comparison", []):
        st.write(f"- {item}")

      commentary_text = result.get("commentary", "No commentary returned.")
      st.subheader(f"Commentary ({language_label})")
      st.info(commentary_text)

      try:
        audio_bytes = generate_tts_audio(commentary_text, selected_language)
        if audio_bytes:
          st.audio(audio_bytes, format="audio/mp3", autoplay=True)
      except Exception as exc:
        st.warning(f"Could not generate commentary audio: {exc}")

      st.subheader("Verdict")
      st.success(result.get("verdict", "No verdict returned."))

      winner = result.get("prediction", "Unknown")
      confidence = result.get("confidence", 0)
      m1, m2 = st.columns(2)
      with m1:
        st.metric("Predicted Winner", winner)
      with m2:
        st.metric("Confidence", f"{confidence}%")