from io import BytesIO
import os
import re
from urllib.parse import quote

from gtts import gTTS
import matplotlib.pyplot as plt
import numpy as np
import requests
import streamlit as st
from stt import transcribe_wav_bytes, extract_players_from_transcript


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
    "rishab": "Rishabh Pant",
    "rishab pant": "Rishabh Pant",
    "rishabh": "Rishabh Pant",
    "sachin": "Sachin Tendulkar",
  "master blaster": "Sachin Tendulkar",
}



st.set_page_config(
    page_title="CricketMind AI",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@600;700&family=Inter:wght@400;500;600&display=swap');

:root {
  --ink: #0f172a;
  --muted: #475569;
  --surface: #eef2f6;
  --panel: #ffffff;
  --line: #d4dce7;
  --brand: #6b4f1d;
  --brand-2: #8a6b2f;
}

html, body, [class*="css"] {
  font-family: 'Inter', sans-serif;
}

.stApp {
  background: linear-gradient(180deg, #f3f6fb 0%, #ecf1f7 100%);
}

section.main > div.block-container {
  max-width: 1120px;
  padding-top: 2rem;
  padding-bottom: 2.5rem;
}

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
  color: var(--ink);
  font-family: 'Rajdhani', sans-serif;
  letter-spacing: 0.02em;
  margin-bottom: 0.4rem;
}

.hero {
  background: linear-gradient(120deg, #f5faf8 0%, #edf5f2 100%);
  border: 1px solid #dacba9;
  border-radius: 12px;
  padding: 20px 22px;
  margin-bottom: 16px;
  box-shadow: 0 6px 16px rgba(107, 79, 29, 0.10);
}

.hero * {
  color: #2f2308 !important;
}

.hero h1 {
  font-size: 2.4rem;
  font-weight: 700;
  margin: 0 0 0.3rem 0;
}

.hero p {
  margin: 0;
  opacity: 0.95;
}

.metric-card {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 12px 14px;
  margin: 8px 0;
}

.metric-title {
  color: var(--muted);
  font-size: 0.82rem;
  letter-spacing: 0.02em;
}

.metric-value {
  font-family: 'Rajdhani', sans-serif;
  color: var(--ink);
  font-size: 1.5rem;
  font-weight: 700;
}

.tag {
  display: inline-block;
  margin-top: 6px;
  border-radius: 6px;
  border: 1px solid var(--line);
  padding: 4px 10px;
  background: #f8fafc;
  color: #334155;
  font-size: 0.77rem;
}

div[data-baseweb="input"] input,
div[data-baseweb="select"] > div {
  background: #ffffff !important;
  border: 1px solid var(--line) !important;
  border-radius: 8px !important;
  color: #0f172a !important;
}

div[data-baseweb="input"] input {
  -webkit-text-fill-color: #0f172a !important;
}

div[data-baseweb="select"] span,
div[data-baseweb="select"] div,
div[data-baseweb="select"] svg {
  color: #0f172a !important;
  fill: #0f172a !important;
}

div[data-testid="stAudioInput"] {
  background: #ffffff !important;
  border: 1px solid var(--line) !important;
  border-radius: 8px !important;
  padding: 6px 8px !important;
}

div[data-testid="stAudioInput"] * {
  color: #0f172a !important;
}

div[data-baseweb="input"] input::placeholder {
  color: #94a3b8 !important;
  opacity: 1 !important;
}

div[data-testid="stSelectbox"] {
  max-width: 280px;
}

.stButton > button {
  width: auto;
  min-width: 168px;
  height: 2.75rem;
  border-radius: 8px;
  border: 1px solid #6b4f1d;
  background: var(--brand);
  color: #ffffff;
  font-family: 'Rajdhani', sans-serif;
  font-weight: 700;
  letter-spacing: 0.02em;
  padding: 0 18px;
}

.stButton > button:hover {
  background: #7c5d24;
  border-color: #7c5d24;
  color: #ffffff;
}

div[data-testid="stMetric"] {
  background: #ffffff;
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 10px 12px;
}

div[data-testid="stAlert"] {
  border-radius: 10px;
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


def player_block(title, stats, format_used, photo_source=None):
    st.markdown(f"### {title}")
    if photo_source:
        st.image(photo_source, width=110)

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


@st.cache_data(show_spinner=False, ttl=86400)
def fetch_player_photo_url(player_name):
    name = str(player_name or "").strip()
    if not name:
        return ""

    try:
        summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(name)}"
        summary_resp = requests.get(summary_url, timeout=8)
        if summary_resp.status_code == 200:
            summary_data = summary_resp.json()
            thumb = (summary_data.get("thumbnail") or {}).get("source")
            if thumb:
                try:
                    image_resp = requests.get(thumb, timeout=8)
                    if image_resp.status_code == 200 and image_resp.content:
                        return image_resp.content
                except requests.RequestException:
                    return thumb
    except requests.RequestException:
        pass

    try:
        search_resp = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": f"{name} cricketer",
                "format": "json",
                "utf8": 1,
            },
            timeout=8,
        )
        if search_resp.status_code == 200:
            search_data = search_resp.json()
            results = (((search_data.get("query") or {}).get("search")) or [])
            if results:
                title = results[0].get("title")
                if title:
                    summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(title)}"
                    summary_resp = requests.get(summary_url, timeout=8)
                    if summary_resp.status_code == 200:
                        summary_data = summary_resp.json()
                        thumb = (summary_data.get("thumbnail") or {}).get("source")
                        if thumb:
                            try:
                                image_resp = requests.get(thumb, timeout=8)
                                if image_resp.status_code == 200 and image_resp.content:
                                    return image_resp.content
                            except requests.RequestException:
                                return thumb
    except requests.RequestException:
        pass

    # Fallback avatar so UI always has a player image slot.
    return (
        "https://ui-avatars.com/api/?"
        f"name={quote(name)}&size=256&background=e2e8f0&color=0f172a&bold=true"
    )


def draw_bar_comparison(name1, name2, stats1, stats2):
  runs1 = to_float(stats1.get("runs"))
  runs2 = to_float(stats2.get("runs"))
  avg1 = to_float(stats1.get("average"))
  avg2 = to_float(stats2.get("average"))
  sr1 = to_float(stats1.get("strike_rate"))
  sr2 = to_float(stats2.get("strike_rate"))

  fig, (ax_runs, ax_other) = plt.subplots(1, 2, figsize=(10.2, 4.2), gridspec_kw={"width_ratios": [1, 1.5]})

  # Runs on its own axis so high values do not flatten Avg/SR bars.
  run_x = np.arange(1)
  width = 0.34
  ax_runs.set_facecolor("#ffffff")
  ax_runs.bar(run_x - width / 2, [runs1], width, label=name1, color="#6b4f1d", alpha=0.9)
  ax_runs.bar(run_x + width / 2, [runs2], width, label=name2, color="#7a7d86", alpha=0.9)
  ax_runs.set_xticks(run_x)
  ax_runs.set_xticklabels(["Runs"])
  ax_runs.set_ylabel("Runs")
  ax_runs.grid(axis="y", alpha=0.25)

  metric_labels = ["Average", "Strike Rate"]
  values1 = [avg1, sr1]
  values2 = [avg2, sr2]
  metric_x = np.arange(len(metric_labels))

  ax_other.set_facecolor("#ffffff")
  ax_other.bar(metric_x - width / 2, values1, width, label=name1, color="#6b4f1d", alpha=0.9)
  ax_other.bar(metric_x + width / 2, values2, width, label=name2, color="#7a7d86", alpha=0.9)
  ax_other.set_xticks(metric_x)
  ax_other.set_xticklabels(metric_labels)
  ax_other.set_ylabel("Value")
  ax_other.grid(axis="y", alpha=0.25)
  ax_other.legend(loc="upper right")

  st.pyplot(fig, use_container_width=True)
  plt.close(fig)


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
if "last_result" not in st.session_state:
  st.session_state.last_result = None
if "last_error" not in st.session_state:
  st.session_state.last_error = ""
if "last_compared_players" not in st.session_state:
  st.session_state.last_compared_players = ("", "")
if "last_language_label" not in st.session_state:
  st.session_state.last_language_label = "English"

# Apply voice-detected players before text inputs are instantiated.
if "pending_player1" in st.session_state and "pending_player2" in st.session_state:
  st.session_state.player1 = st.session_state.pop("pending_player1")
  st.session_state.player2 = st.session_state.pop("pending_player2")

if hasattr(st, "audio_input"):
  st.markdown("### Voice Input")
  st.caption("Please say two player names.")
  voice_clip = st.audio_input("Record your voice")

  if "last_voice_transcript" in st.session_state:
    st.caption(f"Last transcript: {st.session_state.last_voice_transcript}")
  if "last_voice_players" in st.session_state:
    last_p1, last_p2 = st.session_state.last_voice_players
    if last_p1 and last_p2:
      st.info(f"Detected players from voice: {last_p1} vs {last_p2}")

  if st.button("Use Voice Input"):
    if voice_clip is None:
      st.warning("Please record your voice first.")
    else:
      st.caption(
        f"Recorded audio: {getattr(voice_clip, 'name', 'unknown')} ({getattr(voice_clip, 'type', 'unknown')})"
      )
      with st.spinner("Processing voice input..."):
        transcript, stt_error = transcribe_wav_bytes(
          voice_clip.getvalue(),
          language="en",
          filename=getattr(voice_clip, "name", ""),
          mime_type=getattr(voice_clip, "type", ""),
        )

      if stt_error:
        st.error(stt_error)
      else:
        st.session_state.last_voice_transcript = transcript
        st.caption(f"Transcript: {transcript}")
        p1_voice, p2_voice = extract_players_from_transcript(transcript)
        st.session_state.last_voice_players = (p1_voice, p2_voice)
        if not p1_voice or not p2_voice:
          st.warning("Could not detect two player names. Try saying full names clearly.")
        else:
          st.info(f"Detected players from voice: {p1_voice} vs {p2_voice}")
          st.session_state.pending_player1 = p1_voice
          st.session_state.pending_player2 = p2_voice
          st.rerun()

input_col1, input_col2 = st.columns(2)
with input_col1:
    player1 = st.text_input("Player 1", key="player1", placeholder="e.g. Virat Kohli")
with input_col2:
    player2 = st.text_input("Player 2", key="player2", placeholder="e.g. Rohit Sharma")

controls_col1, controls_col2, _ = st.columns([1.15, 0.8, 2.05])
with controls_col1:
  language_label = st.selectbox(
    "Commentary language",
    options=list(LANGUAGE_OPTIONS.keys()),
    index=list(LANGUAGE_OPTIONS.keys()).index(st.session_state.last_language_label),
  )
with controls_col2:
  st.write("")
  compare_clicked = st.button("Compare Players", type="primary")

selected_language = LANGUAGE_OPTIONS[language_label]

if compare_clicked:
  player1_resolved = resolve_player_alias(player1)
  player2_resolved = resolve_player_alias(player2)

  if not player1_resolved.strip() or not player2_resolved.strip():
    st.session_state.last_result = None
    st.session_state.last_error = "Please enter both player names."
  elif player1_resolved.strip().lower() == player2_resolved.strip().lower():
    st.session_state.last_result = None
    st.session_state.last_error = "Please enter two different players."
  else:
    st.session_state.last_error = ""
    if player1_resolved != player1 or player2_resolved != player2:
      st.caption(f"Interpreting input as: {player1_resolved} vs {player2_resolved}")

    with st.spinner("Fetching live stats and generating analysis..."):
      try:
        response = call_backend(player1_resolved, player2_resolved, selected_language)
      except requests.RequestException as exc:
        st.session_state.last_result = None
        st.session_state.last_error = f"Could not reach backend at {BACKEND_URL}: {exc}"
        response = None

      if response is not None and response.status_code != 200:
        st.session_state.last_result = None
        st.session_state.last_error = f"Backend request failed with status code {response.status_code}."

      if response is not None and response.status_code == 200:
        result = response.json()
        if result.get("status") == "error":
          st.session_state.last_result = None
          st.session_state.last_error = result.get("message", "Unknown API error.")
        else:
          analysis = result.get("analysis", {})
          keys = list(analysis.keys())
          if len(keys) < 2:
            st.session_state.last_result = None
            st.session_state.last_error = "Unexpected response format: analysis data missing."
          else:
            st.session_state.last_result = result
            st.session_state.last_compared_players = (player1_resolved, player2_resolved)
            st.session_state.last_language_label = language_label
            st.session_state.last_error = ""

if st.session_state.last_error:
  st.error(st.session_state.last_error)

if st.session_state.last_result:
  result = st.session_state.last_result
  player1_resolved, player2_resolved = st.session_state.last_compared_players
  language_label = st.session_state.last_language_label
  selected_language = LANGUAGE_OPTIONS.get(language_label, "en")
  analysis = result.get("analysis", {})
  keys = list(analysis.keys())
  k1, k2 = keys[0], keys[1]
  stats1, stats2 = analysis[k1], analysis[k2]
  formats = result.get("format_used", {})
  photo1 = fetch_player_photo_url(player1_resolved)
  photo2 = fetch_player_photo_url(player2_resolved)

  st.write("")
  c1, c2 = st.columns(2)
  with c1:
    player_block(player1_resolved.title(), stats1, formats.get("player1", "unknown"), photo1)
  with c2:
    player_block(player2_resolved.title(), stats2, formats.get("player2", "unknown"), photo2)

  st.subheader("Performance Comparison (Bar Chart)")
  draw_bar_comparison(player1_resolved.title(), player2_resolved.title(), stats1, stats2)

  st.subheader("Head-to-Head Insights")
  for item in result.get("comparison", []):
    st.write(f"- {item}")

  commentary_text = result.get("commentary", "No commentary returned.")
  st.subheader(f"Commentary ({language_label})")
  st.info(commentary_text)

  st.subheader("Verdict")
  st.success(result.get("verdict", "No verdict returned."))

  winner = result.get("prediction", "Unknown")
  confidence = result.get("confidence", 0)
  m1, m2 = st.columns(2)
  with m1:
    st.metric("Predicted Winner", winner)
  with m2:
    st.metric("Confidence", f"{confidence}%")

  try:
    st.caption("Generating audio commentary...")
    audio_bytes = generate_tts_audio(commentary_text, selected_language)
    if audio_bytes:
      st.audio(audio_bytes, format="audio/mp3")
  except Exception as exc:
    st.warning(f"Could not generate commentary audio: {exc}")
