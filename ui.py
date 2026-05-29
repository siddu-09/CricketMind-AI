from io import BytesIO
import html
import os
import re
from urllib.parse import quote

from gtts import gTTS
import plotly.graph_objects as go
import requests
import streamlit as st
from stt import transcribe_wav_bytes, extract_players_from_transcript
from players import resolve_player_alias


BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000/analyze")
LANGUAGE_OPTIONS = {
  "English": "en",
  "Hindi": "hi",
  "Kannada": "kn",
}
FORMAT_OPTIONS = {
  "All Formats Combined": "combined",
  "ODI": "odi",
  "T20I": "t20i",
  "Test": "test",
  "IPL": "ipl",
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

.stButton > button,
.stButton > button * {
  color: #ffffff !important;
  fill: #ffffff !important;
}

.stButton > button:hover {
  background: #7c5d24;
  border-color: #7c5d24;
  color: #ffffff;
}

.stButton > button:hover,
.stButton > button:hover * {
  color: #ffffff !important;
  fill: #ffffff !important;
}

.result-banner {
  background: linear-gradient(120deg, #f9fbff 0%, #eef4ff 100%);
  border: 1px solid #cfd9ee;
  border-radius: 12px;
  padding: 14px 16px;
  margin: 10px 0 14px 0;
}

.result-title {
  color: #0f172a;
  font-family: 'Rajdhani', sans-serif;
  font-weight: 700;
  font-size: 1.35rem;
  line-height: 1.1;
}

.result-subtitle {
  margin-top: 3px;
  color: #334155;
  font-size: 0.93rem;
}

.section-card {
  background: #ffffff;
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 14px 16px;
  margin: 10px 0;
}

.section-heading {
  font-family: 'Rajdhani', sans-serif;
  font-size: 1.2rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 8px 0;
}

.insight-list {
  margin: 0;
  padding-left: 18px;
  color: #1f2937;
}

.insight-list li {
  margin: 4px 0;
}

.commentary-text {
  color: #1f2937;
  line-height: 1.5;
}

.verdict-text {
  color: #14532d;
  background: #ecfdf3;
  border: 1px solid #bbf7d0;
  border-radius: 8px;
  padding: 10px 12px;
  font-weight: 600;
}

/* ── Bowling mode metric cards ───────────────────────── */
.metric-card-bowl {
  background: #f0fdf4;
  border: 1px solid #86efac;
  border-radius: 10px;
  padding: 12px 14px;
  margin: 8px 0;
}
.metric-card-bowl .metric-title { color: #15803d; }
.metric-card-bowl .metric-value { color: #14532d; }

.mode-toggle-wrap {
  display: flex;
  align-items: center;
  gap: 0;
  border: 1px solid var(--line);
  border-radius: 8px;
  overflow: hidden;
  width: fit-content;
  margin-top: 2px;
}
.mode-btn {
  padding: 7px 18px;
  font-family: 'Rajdhani', sans-serif;
  font-weight: 700;
  font-size: 0.9rem;
  cursor: pointer;
  border: none;
  background: #f8fafc;
  color: #475569;
  transition: background 0.15s, color 0.15s;
  letter-spacing: 0.02em;
}
.mode-btn.active-bat  { background: #6b4f1d; color: #fff; }
.mode-btn.active-bowl { background: #15803d; color: #fff; }

.bowl-badge {
  display: inline-block;
  background: #dcfce7;
  color: #15803d;
  border: 1px solid #86efac;
  border-radius: 6px;
  padding: 2px 10px;
  font-size: 0.78rem;
  font-weight: 600;
  margin-left: 8px;
  vertical-align: middle;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.summary-item {
  border: 1px solid var(--line);
  border-radius: 10px;
  background: #f8fbff;
  padding: 10px 12px;
}

.summary-label {
  color: #475569;
  font-size: 0.8rem;
}

.summary-value {
  color: #0f172a;
  font-family: 'Rajdhani', sans-serif;
  font-size: 1.35rem;
  font-weight: 700;
}

@media (max-width: 840px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }
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

def draw_radar_comparison(name1, name2, stats1, stats2, key=None):
    stats1 = stats1 or {}
    stats2 = stats2 or {}
    runs1 = to_float(stats1.get("runs"))
    runs2 = to_float(stats2.get("runs"))
    avg1  = to_float(stats1.get("average"))
    avg2  = to_float(stats2.get("average"))
    sr1   = to_float(stats1.get("strike_rate"))
    sr2   = to_float(stats2.get("strike_rate"))

    # Normalise each metric to 0–100 so axes are comparable.
    # Without this, Runs (thousands) would dwarf Avg/SR (tens).
    def normalise(v1, v2):
        m = max(v1, v2, 1)
        return round(v1 / m * 100, 1), round(v2 / m * 100, 1)

    r1n, r2n = normalise(runs1, runs2)
    a1n, a2n = normalise(avg1,  avg2)
    s1n, s2n = normalise(sr1,   sr2)

    categories = ["Runs", "Average", "Strike Rate"]
    # Plotly radar needs the first point repeated to close the polygon.
    vals1 = [r1n, a1n, s1n, r1n]
    vals2 = [r2n, a2n, s2n, r2n]
    cats  = categories + [categories[0]]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=vals1,
        theta=cats,
        name=name1,
        fill="toself",
        line=dict(color="#6b4f1d", width=3),
        fillcolor="rgba(107, 79, 29, 0.2)",
        hovertemplate=(
            f"<b>{name1}</b><br>"
            "Metric: %{theta}<br>"
            "Score: %{r:.1f}<extra></extra>"
        ),
    ))

    fig.add_trace(go.Scatterpolar(
        r=vals2,
        theta=cats,
        name=name2,
        fill="toself",
        line=dict(color="#0284c7", width=3),
        fillcolor="rgba(2, 132, 199, 0.2)",
        hovertemplate=(
            f"<b>{name2}</b><br>"
            "Metric: %{theta}<br>"
            "Score: %{r:.1f}<extra></extra>"
        ),
    ))

    fig.update_layout(
        font=dict(
            family="Inter, sans-serif",
            size=12,
            color="#0f172a"
        ),
        polar=dict(
            bgcolor="#ffffff",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=10, color="#475569"),
                tickvals=[25, 50, 75, 100],
                ticktext=["25%", "50%", "75%", "100%"],
                gridcolor="#e2e8f0",
                linecolor="#cbd5e1",
            ),
            angularaxis=dict(
                tickfont=dict(size=12, color="#0f172a"),
                gridcolor="#e2e8f0",
                linecolor="#cbd5e1",
            ),
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            y=-0.15,
            x=0.5,
            xanchor="center",
            font=dict(size=12, color="#0f172a")
        ),
        margin=dict(t=40, b=80, l=60, r=60),
        height=450,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(fig, use_container_width=True, key=key)


def draw_radar_comparison_bowling(name1, name2, stats1, stats2, key=None):
    """Radar chart for bowling stats. Lower avg/economy = better, so we invert them."""
    stats1 = stats1 or {}
    stats2 = stats2 or {}

    wkts1 = to_float(stats1.get("wickets"))
    wkts2 = to_float(stats2.get("wickets"))
    avg1  = to_float(stats1.get("bowling_average"))
    avg2  = to_float(stats2.get("bowling_average"))
    eco1  = to_float(stats1.get("economy"))
    eco2  = to_float(stats2.get("economy"))
    sr1   = to_float(stats1.get("bowling_sr"))
    sr2   = to_float(stats2.get("bowling_sr"))

    def normalise(v1, v2):
        m = max(v1, v2, 1)
        return round(v1 / m * 100, 1), round(v2 / m * 100, 1)

    def invert_normalise(v1, v2):
        """For avg/economy/sr: lower is better. Invert so bigger bar = better."""
        m = max(v1, v2, 1)
        s1 = round((1 - v1 / m) * 100 + 10, 1) if v1 > 0 else 0
        s2 = round((1 - v2 / m) * 100 + 10, 1) if v2 > 0 else 0
        return s1, s2

    w1n, w2n = normalise(wkts1, wkts2)
    a1n, a2n = invert_normalise(avg1, avg2)
    e1n, e2n = invert_normalise(eco1, eco2)
    s1n, s2n = invert_normalise(sr1, sr2)

    categories = ["Wickets", "Avg (inv)", "Economy (inv)", "Bowl SR (inv)"]
    vals1 = [w1n, a1n, e1n, s1n, w1n]
    vals2 = [w2n, a2n, e2n, s2n, w2n]
    cats  = categories + [categories[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals1, theta=cats, name=name1, fill="toself",
        line=dict(color="#6b4f1d", width=3),
        fillcolor="rgba(107, 79, 29, 0.2)",
        hovertemplate=f"<b>{name1}</b><br>%{{theta}}: %{{r:.1f}}<extra></extra>",
    ))
    fig.add_trace(go.Scatterpolar(
        r=vals2, theta=cats, name=name2, fill="toself",
        line=dict(color="#15803d", width=3),
        fillcolor="rgba(21, 128, 61, 0.2)",
        hovertemplate=f"<b>{name2}</b><br>%{{theta}}: %{{r:.1f}}<extra></extra>",
    ))
    fig.update_layout(
        font=dict(family="Inter, sans-serif", size=12, color="#0f172a"),
        polar=dict(
            bgcolor="#ffffff",
            radialaxis=dict(
                visible=True, range=[0, 110],
                tickfont=dict(size=10, color="#475569"),
                tickvals=[25, 50, 75, 100],
                ticktext=["25", "50", "75", "100"],
                gridcolor="#e2e8f0", linecolor="#cbd5e1",
            ),
            angularaxis=dict(tickfont=dict(size=11, color="#0f172a"), gridcolor="#e2e8f0", linecolor="#cbd5e1"),
        ),
        annotations=[dict(
            text="Avg, Economy & Bowl SR are inverted — higher bar = better",
            x=0.5, y=-0.22, xref="paper", yref="paper",
            showarrow=False, font=dict(size=10, color="#64748b"),
        )],
        showlegend=True,
        legend=dict(orientation="h", y=-0.28, x=0.5, xanchor="center", font=dict(size=12, color="#0f172a")),
        margin=dict(t=40, b=100, l=60, r=60),
        height=470,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True, key=key)


def player_block_bowling(title, stats, format_used, photo_source=None):
    """Metric card for a bowler — shows wickets, bowling avg, economy."""
    st.markdown(f"### {title}")
    if photo_source:
        st.image(photo_source, width=110)
    wkts = stats.get("wickets", "N/A")
    bavg = stats.get("bowling_average", "N/A")
    econ = stats.get("economy", "N/A")
    st.markdown(
        f"""
        <div class="metric-card-bowl">
          <div class="metric-title">Wickets</div>
          <div class="metric-value">{wkts}</div>
        </div>
        <div class="metric-card-bowl">
          <div class="metric-title">Bowling Average</div>
          <div class="metric-value">{bavg}</div>
        </div>
        <div class="metric-card-bowl">
          <div class="metric-title">Economy</div>
          <div class="metric-value">{econ}</div>
        </div>
        <span class="tag" style="background:#f0fdf4;border-color:#86efac;color:#15803d;">Stats Basis: {format_used.upper()}</span>
        """,
        unsafe_allow_html=True,
    )


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


def call_backend(player1, player2, language, match_format, stats_mode="batting"):
    return requests.post(
        BACKEND_URL,
        json={
          "player1": player1.strip(),
          "player2": player2.strip(),
          "language": language,
          "format": match_format,
          "stats_mode": stats_mode,
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
if "last_format_label" not in st.session_state:
  st.session_state.last_format_label = "All Formats Combined"
if "last_stats_mode" not in st.session_state:
  st.session_state.last_stats_mode = "batting"

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

controls_col1, controls_col2, controls_col3, controls_col4 = st.columns([1.1, 1.1, 1.0, 1.3])
with controls_col1:
  language_label = st.selectbox(
    "Commentary language",
    options=list(LANGUAGE_OPTIONS.keys()),
    index=list(LANGUAGE_OPTIONS.keys()).index(st.session_state.last_language_label),
  )
with controls_col2:
  format_label = st.selectbox(
    "Match format",
    options=list(FORMAT_OPTIONS.keys()),
    index=list(FORMAT_OPTIONS.keys()).index(st.session_state.last_format_label),
  )
with controls_col3:
  stats_mode_label = st.radio(
    "Stats mode",
    options=["Batting", "Bowling"],
    index=0 if st.session_state.last_stats_mode == "batting" else 1,
    horizontal=True,
  )
  selected_stats_mode = "bowling" if "Bowling" in stats_mode_label else "batting"
with controls_col4:
  st.write("")
  st.write("")
  compare_clicked = st.button("Compare Players", type="primary")

selected_language = LANGUAGE_OPTIONS[language_label]
selected_format = FORMAT_OPTIONS[format_label]

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
        response = call_backend(player1_resolved, player2_resolved, selected_language, selected_format, selected_stats_mode)
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
            st.session_state.last_format_label = format_label
            st.session_state.last_stats_mode = selected_stats_mode
            st.session_state.last_error = ""

if st.session_state.last_error:
  st.error(st.session_state.last_error)

if st.session_state.last_result:
  result = st.session_state.last_result
  player1_resolved, player2_resolved = st.session_state.last_compared_players
  language_label = st.session_state.last_language_label
  selected_language = LANGUAGE_OPTIONS.get(language_label, "en")
  active_mode = result.get("stats_mode", st.session_state.get("last_stats_mode", "batting"))
  analysis = result.get("analysis", {})
  keys = list(analysis.keys())
  k1, k2 = keys[0], keys[1]
  stats1, stats2 = analysis[k1], analysis[k2]
  formats = result.get("format_used", {})
  photo1 = fetch_player_photo_url(player1_resolved)
  photo2 = fetch_player_photo_url(player2_resolved)

  mode_badge = '<span class="bowl-badge">Bowling Mode</span>' if active_mode == "bowling" else ""
  st.markdown(
    f"""
    <div class="result-banner">
      <div class="result-title">Comparison Ready {mode_badge}</div>
      <div class="result-subtitle">{html.escape(player1_resolved.title())} vs {html.escape(player2_resolved.title())}</div>
    </div>
    """,
    unsafe_allow_html=True,
  )

  st.write("")
  c1, c2 = st.columns(2)

  if active_mode == "bowling":
    # ── BOWLING: player metric cards ──
    with c1:
      player_block_bowling(player1_resolved.title(), stats1, formats.get("player1", "unknown"), photo1)
    with c2:
      player_block_bowling(player2_resolved.title(), stats2, formats.get("player2", "unknown"), photo2)
  else:
    with c1:
      player_block(player1_resolved.title(), stats1, formats.get("player1", "unknown"), photo1)
    with c2:
      player_block(player2_resolved.title(), stats2, formats.get("player2", "unknown"), photo2)

  st.subheader("Performance Comparison")
  c_graph, c_table = st.columns([1.1, 0.9])

  breakdown = result.get("format_breakdown", {})
  bowl_breakdown = result.get("bowling_breakdown", {})
  p1_breakdown = breakdown.get("player1", {})
  p2_breakdown = breakdown.get("player2", {})
  p1_bowl_bd = bowl_breakdown.get("player1", {})
  p2_bowl_bd = bowl_breakdown.get("player2", {})

  with c_graph:
    tab_overview, tab_test, tab_odi, tab_t20i, tab_ipl = st.tabs(["Overview", "Test", "ODI", "T20I", "IPL"])

    if active_mode == "bowling":
      with tab_overview:
        draw_radar_comparison_bowling(player1_resolved.title(), player2_resolved.title(), stats1, stats2, key="bowl_radar_overview")
      with tab_test:
        t1 = p1_bowl_bd.get("test", {}); t2 = p2_bowl_bd.get("test", {})
        if t1 or t2: draw_radar_comparison_bowling(player1_resolved.title(), player2_resolved.title(), t1, t2, key="bowl_radar_test")
        else: st.info("No Test bowling statistics available.")
      with tab_odi:
        o1 = p1_bowl_bd.get("odi", {}); o2 = p2_bowl_bd.get("odi", {})
        if o1 or o2: draw_radar_comparison_bowling(player1_resolved.title(), player2_resolved.title(), o1, o2, key="bowl_radar_odi")
        else: st.info("No ODI bowling statistics available.")
      with tab_t20i:
        t1 = p1_bowl_bd.get("t20i", {}); t2 = p2_bowl_bd.get("t20i", {})
        if t1 or t2: draw_radar_comparison_bowling(player1_resolved.title(), player2_resolved.title(), t1, t2, key="bowl_radar_t20i")
        else: st.info("No T20I bowling statistics available.")
      with tab_ipl:
        i1 = p1_bowl_bd.get("ipl", {}); i2 = p2_bowl_bd.get("ipl", {})
        if i1 or i2: draw_radar_comparison_bowling(player1_resolved.title(), player2_resolved.title(), i1, i2, key="bowl_radar_ipl")
        else: st.info("No IPL bowling statistics available.")
    else:
      with tab_overview:
        draw_radar_comparison(player1_resolved.title(), player2_resolved.title(), stats1, stats2, key="radar_overview")
      with tab_test:
        test1 = p1_breakdown.get("test", {}); test2 = p2_breakdown.get("test", {})
        if test1 or test2: draw_radar_comparison(player1_resolved.title(), player2_resolved.title(), test1, test2, key="radar_test")
        else: st.info("No Test match statistics available for comparison.")
      with tab_odi:
        odi1 = p1_breakdown.get("odi", {}); odi2 = p2_breakdown.get("odi", {})
        if odi1 or odi2: draw_radar_comparison(player1_resolved.title(), player2_resolved.title(), odi1, odi2, key="radar_odi")
        else: st.info("No ODI match statistics available for comparison.")
      with tab_t20i:
        t20i1 = p1_breakdown.get("t20i", {}); t20i2 = p2_breakdown.get("t20i", {})
        if t20i1 or t20i2: draw_radar_comparison(player1_resolved.title(), player2_resolved.title(), t20i1, t20i2, key="radar_t20i")
        else: st.info("No T20I match statistics available for comparison.")
      with tab_ipl:
        ipl1 = p1_breakdown.get("ipl", {}); ipl2 = p2_breakdown.get("ipl", {})
        if ipl1 or ipl2: draw_radar_comparison(player1_resolved.title(), player2_resolved.title(), ipl1, ipl2, key="radar_ipl")
        else: st.info("No IPL statistics available for comparison.")

  with c_table:
    if active_mode == "bowling" and bowl_breakdown:
      table_rows = ""
      for fmt_name, fmt_lbl in [("test","TEST"),("odi","ODI"),("t20i","T20I"),("ipl","IPL")]:
        p1f = p1_bowl_bd.get(fmt_name, {}); p2f = p2_bowl_bd.get(fmt_name, {})
        if p1f or p2f:
          table_rows += f"""
          <tr style="background:#f0fdf4;font-weight:bold;border-top:2px solid var(--line);">
            <td colspan="3" style="padding:10px;color:#15803d;text-transform:uppercase;font-family:'Rajdhani',sans-serif;font-size:1.1rem;">{fmt_lbl}</td>
          </tr>
          <tr style="border-bottom:1px solid #e2e8f0;">
            <td style="padding:8px 12px;color:var(--muted);font-size:0.9rem;">Wickets</td>
            <td style="padding:8px 12px;text-align:center;font-weight:600;color:var(--ink);">{p1f.get('wickets','N/A')}</td>
            <td style="padding:8px 12px;text-align:center;font-weight:600;color:var(--ink);">{p2f.get('wickets','N/A')}</td>
          </tr>
          <tr style="border-bottom:1px solid #e2e8f0;">
            <td style="padding:8px 12px;color:var(--muted);font-size:0.9rem;">Bowl Average</td>
            <td style="padding:8px 12px;text-align:center;font-weight:600;color:var(--ink);">{p1f.get('bowling_average','N/A')}</td>
            <td style="padding:8px 12px;text-align:center;font-weight:600;color:var(--ink);">{p2f.get('bowling_average','N/A')}</td>
          </tr>
          <tr style="border-bottom:1px solid #e2e8f0;">
            <td style="padding:8px 12px;color:var(--muted);font-size:0.9rem;">Economy</td>
            <td style="padding:8px 12px;text-align:center;font-weight:600;color:var(--ink);">{p1f.get('economy','N/A')}</td>
            <td style="padding:8px 12px;text-align:center;font-weight:600;color:var(--ink);">{p2f.get('economy','N/A')}</td>
          </tr>
          <tr style="border-bottom:1px solid #cbd5e1;">
            <td style="padding:8px 12px;color:var(--muted);font-size:0.9rem;">Bowl Strike Rate</td>
            <td style="padding:8px 12px;text-align:center;font-weight:600;color:var(--ink);">{p1f.get('bowling_sr','N/A')}</td>
            <td style="padding:8px 12px;text-align:center;font-weight:600;color:var(--ink);">{p2f.get('bowling_sr','N/A')}</td>
          </tr>
          """
      st.markdown(
        f"""
        <div class="section-card" style="margin:0;padding:16px;">
          <div class="section-heading" style="margin-bottom:12px;">Bowling Format Breakdown</div>
          <table style="width:100%;border-collapse:collapse;border:1px solid var(--line);border-radius:8px;overflow:hidden;">
            <thead>
              <tr style="background:#f0fdf4;border-bottom:2px solid #86efac;">
                <th style="padding:10px;text-align:left;color:var(--ink);font-family:'Rajdhani',sans-serif;font-weight:700;">Metric</th>
                <th style="padding:10px;text-align:center;color:var(--ink);font-family:'Rajdhani',sans-serif;font-weight:700;width:35%;">{html.escape(player1_resolved.title())}</th>
                <th style="padding:10px;text-align:center;color:var(--ink);font-family:'Rajdhani',sans-serif;font-weight:700;width:35%;">{html.escape(player2_resolved.title())}</th>
              </tr>
            </thead>
            <tbody>{table_rows}</tbody>
          </table>
        </div>
        """,
        unsafe_allow_html=True,
      )
    elif breakdown:
      table_rows = ""
      for fmt_name, fmt_label_t in [("test","TEST"),("odi","ODI"),("t20i","T20I"),("ipl","IPL")]:
        p1_fmt = p1_breakdown.get(fmt_name, {}); p2_fmt = p2_breakdown.get(fmt_name, {})
        if p1_fmt or p2_fmt:
          table_rows += f"""
          <tr style="background-color: #f8fbff; font-weight: bold; border-top: 2px solid var(--line);">
            <td colspan="3" style="padding: 10px; color: var(--brand); text-transform: uppercase; font-family: 'Rajdhani', sans-serif; font-size: 1.1rem;">{fmt_label_t}</td>
          </tr>
          <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 8px 12px; color: var(--muted); font-size: 0.9rem;">Innings</td>
            <td style="padding: 8px 12px; text-align: center; color: var(--ink);">{p1_fmt.get('innings', 'N/A')}</td>
            <td style="padding: 8px 12px; text-align: center; color: var(--ink);">{p2_fmt.get('innings', 'N/A')}</td>
          </tr>
          <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 8px 12px; color: var(--muted); font-size: 0.9rem;">Runs</td>
            <td style="padding: 8px 12px; text-align: center; font-weight: 600; color: var(--ink);">{p1_fmt.get('runs', 'N/A')}</td>
            <td style="padding: 8px 12px; text-align: center; font-weight: 600; color: var(--ink);">{p2_fmt.get('runs', 'N/A')}</td>
          </tr>
          <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 8px 12px; color: var(--muted); font-size: 0.9rem;">Average</td>
            <td style="padding: 8px 12px; text-align: center; font-weight: 600; color: var(--ink);">{p1_fmt.get('average', 'N/A')}</td>
            <td style="padding: 8px 12px; text-align: center; font-weight: 600; color: var(--ink);">{p2_fmt.get('average', 'N/A')}</td>
          </tr>
          <tr style="border-bottom: 1px solid #cbd5e1;">
            <td style="padding: 8px 12px; color: var(--muted); font-size: 0.9rem;">Strike Rate</td>
            <td style="padding: 8px 12px; text-align: center; font-weight: 600; color: var(--ink);">{p1_fmt.get('strike_rate', 'N/A')}</td>
            <td style="padding: 8px 12px; text-align: center; font-weight: 600; color: var(--ink);">{p2_fmt.get('strike_rate', 'N/A')}</td>
          </tr>
          """
      st.markdown(
        f"""
        <div class="section-card" style="margin: 0; padding: 16px;">
          <div class="section-heading" style="margin-bottom: 12px;">Format Stats Breakdown</div>
          <table style="width: 100%; border-collapse: collapse; border: 1px solid var(--line); border-radius: 8px; overflow: hidden;">
            <thead>
              <tr style="background-color: #f1f5f9; border-bottom: 2px solid var(--line);">
                <th style="padding: 10px; text-align: left; color: var(--ink); font-family: 'Rajdhani', sans-serif; font-weight: 700;">Metric</th>
                <th style="padding: 10px; text-align: center; color: var(--ink); font-family: 'Rajdhani', sans-serif; font-weight: 700; width: 35%;">{html.escape(player1_resolved.title())}</th>
                <th style="padding: 10px; text-align: center; color: var(--ink); font-family: 'Rajdhani', sans-serif; font-weight: 700; width: 35%;">{html.escape(player2_resolved.title())}</th>
              </tr>
            </thead>
            <tbody>
              {table_rows}
            </tbody>
          </table>
        </div>
        """,
        unsafe_allow_html=True,
      )
    else:
      st.caption("Detailed format breakdown not available.")

  st.write("")
  st.subheader("Deep Dive Analysis & Splits")
  tab_h2h, tab_splits, tab_situational, tab_timeline = st.tabs([
      "Head-to-Head & Form", 
      "Venue & Opposition Splits", 
      "Situational Records", 
      "Career Timeline"
  ])

  p1_det = result.get("player1_details", {})
  p2_det = result.get("player2_details", {})

  with tab_h2h:
      # ── Recent Form Section ──
      st.markdown("##### Recent Form (Last 5 Innings)")
      rf1, rf2 = st.columns(2)
      with rf1:
          st.markdown(f"**{player1_resolved.title()}**")
          form_html1 = ""
          for score in p1_det.get("recent_form", []):
              is_good = False
              if active_mode == "bowling":
                  try:
                      w = int(score.split("/")[0])
                      is_good = w >= 2
                  except:
                      pass
              else:
                  try:
                      s = int(score.replace("*", ""))
                      is_good = s >= 50
                  except:
                      pass
              bg = "#ecfdf5" if is_good else "#f8fafc"
              border = "#bbf7d0" if is_good else "#e2e8f0"
              color = "#10b981" if is_good else "#475569"
              form_html1 += f'<span style="display:inline-block;padding:6px 12px;margin:2px 4px;border-radius:16px;background:{bg};border:1px solid {border};color:{color};font-weight:700;font-size:0.9rem;">{score}</span>'
          st.markdown(f'<div style="margin-bottom:15px;">{form_html1}</div>', unsafe_allow_html=True)
          
      with rf2:
          st.markdown(f"**{player2_resolved.title()}**")
          form_html2 = ""
          for score in p2_det.get("recent_form", []):
              is_good = False
              if active_mode == "bowling":
                  try:
                      w = int(score.split("/")[0])
                      is_good = w >= 2
                  except:
                      pass
              else:
                  try:
                      s = int(score.replace("*", ""))
                      is_good = s >= 50
                  except:
                      pass
              bg = "#ecfdf5" if is_good else "#f8fafc"
              border = "#bbf7d0" if is_good else "#e2e8f0"
              color = "#10b981" if is_good else "#475569"
              form_html2 += f'<span style="display:inline-block;padding:6px 12px;margin:2px 4px;border-radius:16px;background:{bg};border:1px solid {border};color:{color};font-weight:700;font-size:0.9rem;">{score}</span>'
          st.markdown(f'<div style="margin-bottom:15px;">{form_html2}</div>', unsafe_allow_html=True)
          
      # ── Head-to-Head Section ──
      h2h = result.get("head_to_head")
      if h2h:
          st.markdown("##### Direct Head-to-Head Matchup")
          if h2h.get("type") == "batter_vs_bowler":
              batter = h2h.get("batter")
              bowler = h2h.get("bowler")
              st.markdown(
                  f"""
                  <div class="result-banner" style="background:linear-gradient(120deg, #fefafd 0%, #faf0f7 100%);border-color:#eab8e4;padding:16px;border-radius:12px;margin:0;">
                      <div style="font-family:'Rajdhani',sans-serif;font-size:1.4rem;font-weight:700;color:#701a65;margin-bottom:10px;text-transform:uppercase;letter-spacing:0.02em;">
                          🔥 Matchup: {html.escape(batter)} vs {html.escape(bowler)}
                      </div>
                      <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(120px, 1fr));gap:12px;">
                          <div class="summary-item" style="background:#fff;border-color:#f3d5ef;padding:8px 12px;">
                              <div class="summary-label" style="color:#a24996;">Matches</div>
                              <div class="summary-value" style="color:#701a65;font-size:1.6rem;">{h2h.get('matches')}</div>
                          </div>
                          <div class="summary-item" style="background:#fff;border-color:#f3d5ef;padding:8px 12px;">
                              <div class="summary-label" style="color:#a24996;">Balls Faced</div>
                              <div class="summary-value" style="color:#701a65;font-size:1.6rem;">{h2h.get('balls')}</div>
                          </div>
                          <div class="summary-item" style="background:#fff;border-color:#f3d5ef;padding:8px 12px;">
                              <div class="summary-label" style="color:#a24996;">Runs Scored</div>
                              <div class="summary-value" style="color:#701a65;font-size:1.6rem;">{h2h.get('runs')}</div>
                          </div>
                          <div class="summary-item" style="background:#fff;border-color:#f3d5ef;padding:8px 12px;">
                              <div class="summary-label" style="color:#a24996;">Dismissals</div>
                              <div class="summary-value" style="color:#dc2626;font-size:1.6rem;font-weight:800;">{h2h.get('dismissals')}</div>
                          </div>
                          <div class="summary-item" style="background:#fff;border-color:#f3d5ef;padding:8px 12px;">
                              <div class="summary-label" style="color:#a24996;">Strike Rate</div>
                              <div class="summary-value" style="color:#701a65;font-size:1.6rem;">{h2h.get('strike_rate')}</div>
                          </div>
                      </div>
                      <div style="margin-top:12px;font-size:0.85rem;color:#a24996;font-weight:500;">
                          Matchup breakdown: Dots: <b>{h2h.get('dots')}</b> | Fours: <b>{h2h.get('fours')}</b> | Sixes: <b>{h2h.get('sixes')}</b>
                      </div>
                  </div>
                  """,
                  unsafe_allow_html=True
              )
          elif h2h.get("type") == "batter_comparison":
              p1_h2h = h2h.get("player1", {})
              p2_h2h = h2h.get("player2", {})
              st.markdown(
                  f"""
                  <div class="result-banner" style="background:linear-gradient(120deg, #fbfaff 0%, #f5f2ff 100%);border-color:#cbd2ee;padding:16px;border-radius:12px;margin:0;">
                      <div style="font-family:'Rajdhani',sans-serif;font-size:1.3rem;font-weight:700;color:#2e1a47;margin-bottom:10px;text-transform:uppercase;">
                          🏏 Head-to-Head Career in Shared Matches ({h2h.get('matches')} games)
                      </div>
                      <table style="width:100%;border-collapse:collapse;font-size:0.95rem;background:#fff;border-radius:8px;overflow:hidden;border:1px solid #cbd2ee;">
                          <thead>
                              <tr style="background:#f1eff7;border-bottom:2px solid #cbd5e1;">
                                  <th style="padding:10px;text-align:left;color:var(--ink);">Player</th>
                                  <th style="padding:10px;text-align:center;color:var(--ink);">Runs Scored</th>
                                  <th style="padding:10px;text-align:center;color:var(--ink);">Average</th>
                                  <th style="padding:10px;text-align:center;color:var(--ink);">Strike Rate</th>
                              </tr>
                          </thead>
                          <tbody>
                              <tr style="border-bottom:1px solid #e2e8f0;">
                                  <td style="padding:10px;font-weight:600;color:var(--ink);">{html.escape(player1_resolved.title())}</td>
                                  <td style="padding:10px;text-align:center;font-weight:700;color:var(--brand);">{p1_h2h.get('runs')}</td>
                                  <td style="padding:10px;text-align:center;font-weight:600;color:var(--ink);">{p1_h2h.get('average')}</td>
                                  <td style="padding:10px;text-align:center;font-weight:600;color:var(--ink);">{p1_h2h.get('strike_rate')}</td>
                              </tr>
                              <tr>
                                  <td style="padding:10px;font-weight:600;color:var(--ink);">{html.escape(player2_resolved.title())}</td>
                                  <td style="padding:10px;text-align:center;font-weight:700;color:#0284c7;">{p2_h2h.get('runs')}</td>
                                  <td style="padding:10px;text-align:center;font-weight:600;color:var(--ink);">{p2_h2h.get('average')}</td>
                                  <td style="padding:10px;text-align:center;font-weight:600;color:var(--ink);">{p2_h2h.get('strike_rate')}</td>
                              </tr>
                          </tbody>
                      </table>
                  </div>
                  """,
                  unsafe_allow_html=True
              )
          elif h2h.get("type") == "bowler_comparison":
              p1_h2h = h2h.get("player1", {})
              p2_h2h = h2h.get("player2", {})
              st.markdown(
                  f"""
                  <div class="result-banner" style="background:linear-gradient(120deg, #f0fdf4 0%, #e8f9ed 100%);border-color:#bbf7d0;padding:16px;border-radius:12px;margin:0;">
                      <div style="font-family:'Rajdhani',sans-serif;font-size:1.3rem;font-weight:700;color:#14532d;margin-bottom:10px;text-transform:uppercase;">
                          🏏 Head-to-Head Career in Shared Matches ({h2h.get('matches')} games)
                      </div>
                      <table style="width:100%;border-collapse:collapse;font-size:0.95rem;background:#fff;border-radius:8px;overflow:hidden;border:1px solid #bbf7d0;">
                          <thead>
                              <tr style="background:#eefdf3;border-bottom:2px solid #86efac;">
                                  <th style="padding:10px;text-align:left;color:#15803d;">Player</th>
                                  <th style="padding:10px;text-align:center;color:#15803d;">Wickets Taken</th>
                                  <th style="padding:10px;text-align:center;color:#15803d;">Overs Bowled</th>
                                  <th style="padding:10px;text-align:center;color:#15803d;">Bowling Average</th>
                                  <th style="padding:10px;text-align:center;color:#15803d;">Economy Rate</th>
                              </tr>
                          </thead>
                          <tbody>
                              <tr style="border-bottom:1px solid #e2e8f0;">
                                  <td style="padding:10px;font-weight:600;color:var(--ink);">{html.escape(player1_resolved.title())}</td>
                                  <td style="padding:10px;text-align:center;font-weight:700;color:#16a34a;">{p1_h2h.get('wickets')}</td>
                                  <td style="padding:10px;text-align:center;font-weight:600;color:var(--ink);">{p1_h2h.get('overs')}</td>
                                  <td style="padding:10px;text-align:center;font-weight:600;color:var(--ink);">{p1_h2h.get('average')}</td>
                                  <td style="padding:10px;text-align:center;font-weight:600;color:var(--ink);">{p1_h2h.get('economy')}</td>
                              </tr>
                              <tr>
                                  <td style="padding:10px;font-weight:600;color:var(--ink);">{html.escape(player2_resolved.title())}</td>
                                  <td style="padding:10px;text-align:center;font-weight:700;color:#0284c7;">{p2_h2h.get('wickets')}</td>
                                  <td style="padding:10px;text-align:center;font-weight:600;color:var(--ink);">{p2_h2h.get('overs')}</td>
                                  <td style="padding:10px;text-align:center;font-weight:600;color:var(--ink);">{p2_h2h.get('average')}</td>
                                  <td style="padding:10px;text-align:center;font-weight:600;color:var(--ink);">{p2_h2h.get('economy')}</td>
                              </tr>
                          </tbody>
                      </table>
                  </div>
                  """,
                  unsafe_allow_html=True
              )

  with tab_splits:
      col_v, col_o = st.columns(2)
      val1_label = "Avg" if active_mode == "batting" else "Bowl Avg"
      val2_label = "Strike Rate" if active_mode == "batting" else "Economy"
      
      with col_v:
          st.markdown("##### Venue Performance Splits")
          v1 = p1_det.get("venue_splits", {})
          v2 = p2_det.get("venue_splits", {})
          venue_rows = ""
          for v in ["Home", "Away", "Neutral"]:
              d1 = v1.get(v, {})
              d2 = v2.get(v, {})
              venue_rows += f"""
              <tr style="border-bottom:1px solid #e2e8f0;">
                  <td style="padding:8px 12px;font-weight:bold;color:var(--muted);">{v}</td>
                  <td style="padding:8px 12px;text-align:center;color:var(--brand);font-weight:600;">{d1.get('avg')}<br><span style="font-size:0.75rem;color:var(--muted);font-weight:normal;">{d1.get('sr_or_econ')}</span></td>
                  <td style="padding:8px 12px;text-align:center;color:#0284c7;font-weight:600;">{d2.get('avg')}<br><span style="font-size:0.75rem;color:var(--muted);font-weight:normal;">{d2.get('sr_or_econ')}</span></td>
              </tr>
              """
          st.markdown(
              f"""
              <table style="width:100%;border-collapse:collapse;border:1px solid var(--line);border-radius:8px;overflow:hidden;">
                  <thead>
                      <tr style="background:#f8fafc;border-bottom:2px solid var(--line);">
                          <th style="padding:8px 12px;text-align:left;color:var(--ink);">Venue</th>
                          <th style="padding:8px 12px;text-align:center;color:var(--ink);width:35%;">{html.escape(player1_resolved.title())}<br><span style="font-size:0.75rem;font-weight:normal;color:var(--muted);">{val1_label} / {val2_label}</span></th>
                          <th style="padding:8px 12px;text-align:center;color:var(--ink);width:35%;">{html.escape(player2_resolved.title())}<br><span style="font-size:0.75rem;font-weight:normal;color:var(--muted);">{val1_label} / {val2_label}</span></th>
                      </tr>
                  </thead>
                  <tbody>{venue_rows}</tbody>
              </table>
              """,
              unsafe_allow_html=True
          )
          
      with col_o:
          st.markdown("##### Opposition Performance Splits")
          o1 = p1_det.get("opposition_splits", {})
          o2 = p2_det.get("opposition_splits", {})
          opp_rows = ""
          for opp in sorted(list(o1.keys())):
              d1 = o1.get(opp, {})
              d2 = o2.get(opp, {})
              opp_rows += f"""
              <tr style="border-bottom:1px solid #e2e8f0;">
                  <td style="padding:8px 12px;font-weight:bold;color:var(--muted);">{opp}</td>
                  <td style="padding:8px 12px;text-align:center;color:var(--brand);font-weight:600;">{d1.get('avg')}<br><span style="font-size:0.75rem;color:var(--muted);font-weight:normal;">{d1.get('sr_or_econ')}</span></td>
                  <td style="padding:8px 12px;text-align:center;color:#0284c7;font-weight:600;">{d2.get('avg')}<br><span style="font-size:0.75rem;color:var(--muted);font-weight:normal;">{d2.get('sr_or_econ')}</span></td>
              </tr>
              """
          st.markdown(
              f"""
              <table style="width:100%;border-collapse:collapse;border:1px solid var(--line);border-radius:8px;overflow:hidden;">
                  <thead>
                      <tr style="background:#f8fafc;border-bottom:2px solid var(--line);">
                          <th style="padding:8px 12px;text-align:left;color:var(--ink);">Opposition</th>
                          <th style="padding:8px 12px;text-align:center;color:var(--ink);width:35%;">{html.escape(player1_resolved.title())}<br><span style="font-size:0.75rem;font-weight:normal;color:var(--muted);">{val1_label} / {val2_label}</span></th>
                          <th style="padding:8px 12px;text-align:center;color:var(--ink);width:35%;">{html.escape(player2_resolved.title())}<br><span style="font-size:0.75rem;font-weight:normal;color:var(--muted);">{val1_label} / {val2_label}</span></th>
                      </tr>
                  </thead>
                  <tbody>{opp_rows}</tbody>
              </table>
              """,
              unsafe_allow_html=True
          )

  with tab_situational:
      col_c, col_p = st.columns(2)
      val1_label = "Avg" if active_mode == "batting" else "Bowl Avg"
      val2_label = "SR" if active_mode == "batting" else "Econ"
      
      with col_c:
          st.markdown("##### Innings Situation: Chasing vs Setting Target")
          ch1 = s1.get("chasing", {}); ch2 = s2.get("chasing", {})
          se1 = s1.get("setting", {}); se2 = s2.get("setting", {})
          st.markdown(
              f"""
              <div style="background:#fff;border:1px solid var(--line);border-radius:8px;padding:16px;">
                  <div style="display:flex;justify-content:space-between;border-bottom:1px solid #cbd5e1;padding-bottom:8px;margin-bottom:8px;">
                      <span style="font-weight:bold;color:#475569;">Innings / Situation</span>
                      <span style="font-weight:bold;color:var(--brand);width:35%;text-align:center;">{html.escape(player1_resolved.title())}</span>
                      <span style="font-weight:bold;color:#0284c7;width:35%;text-align:center;">{html.escape(player2_resolved.title())}</span>
                  </div>
                  <div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px dashed #e2e8f0;">
                      <span style="color:#64748b;">Chasing Target</span>
                      <span style="width:35%;text-align:center;font-weight:600;color:var(--ink);">{ch1.get('avg')} <span style="font-size:0.75rem;color:#94a3b8;">({ch1.get('sr_or_econ')})</span></span>
                      <span style="width:35%;text-align:center;font-weight:600;color:var(--ink);">{ch2.get('avg')} <span style="font-size:0.75rem;color:#94a3b8;">({ch2.get('sr_or_econ')})</span></span>
                  </div>
                  <div style="display:flex;justify-content:space-between;padding:6px 0;">
                      <span style="color:#64748b;">Setting Target</span>
                      <span style="width:35%;text-align:center;font-weight:600;color:var(--ink);">{se1.get('avg')} <span style="font-size:0.75rem;color:#94a3b8;">({se1.get('sr_or_econ')})</span></span>
                      <span style="width:35%;text-align:center;font-weight:600;color:var(--ink);">{se2.get('avg')} <span style="font-size:0.75rem;color:#94a3b8;">({se2.get('sr_or_econ')})</span></span>
                  </div>
                  <div style="margin-top:12px;font-size:0.75rem;color:var(--muted);text-align:center;">Format: <b>{val1_label}</b> (<b>{val2_label}</b>)</div>
              </div>
              """,
              unsafe_allow_html=True
          )
          
      with col_p:
          st.markdown("##### Delivery Type: vs Pace vs vs Spin")
          pa1 = s1.get("vs_pace", {}); pa2 = s2.get("vs_pace", {})
          sp1 = s1.get("vs_spin", {}); sp2 = s2.get("vs_spin", {})
          st.markdown(
              f"""
              <div style="background:#fff;border:1px solid var(--line);border-radius:8px;padding:16px;">
                  <div style="display:flex;justify-content:space-between;border-bottom:1px solid #cbd5e1;padding-bottom:8px;margin-bottom:8px;">
                      <span style="font-weight:bold;color:#475569;">Delivery Type</span>
                      <span style="font-weight:bold;color:var(--brand);width:35%;text-align:center;">{html.escape(player1_resolved.title())}</span>
                      <span style="font-weight:bold;color:#0284c7;width:35%;text-align:center;">{html.escape(player2_resolved.title())}</span>
                  </div>
                  <div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px dashed #e2e8f0;">
                      <span style="color:#64748b;">vs Pace Bowlers</span>
                      <span style="width:35%;text-align:center;font-weight:600;color:var(--ink);">{pa1.get('avg')} <span style="font-size:0.75rem;color:#94a3b8;">({pa1.get('sr_or_econ')})</span></span>
                      <span style="width:35%;text-align:center;font-weight:600;color:var(--ink);">{pa2.get('avg')} <span style="font-size:0.75rem;color:#94a3b8;">({pa2.get('sr_or_econ')})</span></span>
                  </div>
                  <div style="display:flex;justify-content:space-between;padding:6px 0;">
                      <span style="color:#64748b;">vs Spin Bowlers</span>
                      <span style="width:35%;text-align:center;font-weight:600;color:var(--ink);">{sp1.get('avg')} <span style="font-size:0.75rem;color:#94a3b8;">({sp1.get('sr_or_econ')})</span></span>
                      <span style="width:35%;text-align:center;font-weight:600;color:var(--ink);">{sp2.get('avg')} <span style="font-size:0.75rem;color:#94a3b8;">({sp2.get('sr_or_econ')})</span></span>
                  </div>
                  <div style="margin-top:12px;font-size:0.75rem;color:var(--muted);text-align:center;">Format: <b>{val1_label}</b> (<b>{val2_label}</b>)</div>
              </div>
              """,
              unsafe_allow_html=True
          )

  with tab_timeline:
      t1 = p1_det.get("timeline", [])
      t2 = p2_det.get("timeline", [])
      if t1 and t2:
          years = [item["year"] for item in t1]
          v1 = [item["value"] for item in t1]
          v2 = [item["value"] for item in t2]
          
          fig_timeline = go.Figure()
          fig_timeline.add_trace(go.Scatter(
              x=years, y=v1, name=player1_resolved.title(),
              line=dict(color="#6b4f1d", width=3),
              marker=dict(size=8, symbol="circle"),
              mode="lines+markers"
          ))
          fig_timeline.add_trace(go.Scatter(
              x=years, y=v2, name=player2_resolved.title(),
              line=dict(color="#0284c7", width=3),
              marker=dict(size=8, symbol="circle"),
              mode="lines+markers"
          ))
          
          chart_title = "Yearly Bowling Average (lower is better)" if active_mode == "bowling" else "Yearly Batting Average"
          fig_timeline.update_layout(
              font=dict(family="Inter, sans-serif", size=12, color="#0f172a"),
              title=dict(text=chart_title, x=0.5, xanchor="center", font=dict(family="Rajdhani, sans-serif", size=16, color="#0f172a", weight="bold")),
              xaxis=dict(tickmode="linear", tick0=2018, dtick=1, gridcolor="#e2e8f0"),
              yaxis=dict(gridcolor="#e2e8f0", title="Average"),
              hovermode="x unified",
              paper_bgcolor="rgba(0,0,0,0)",
              plot_bgcolor="rgba(0,0,0,0)",
              margin=dict(t=50, b=30, l=40, r=40),
              height=360
          )
          st.plotly_chart(fig_timeline, use_container_width=True, key="career_timeline_plotly")
      else:
          st.caption("Career timeline statistics not available.")

  insight_items = result.get("comparison", [])
  safe_insights = "".join(f"<li>{html.escape(str(item))}</li>" for item in insight_items)
  st.markdown(
    f"""
    <div class="section-card">
      <div class="section-heading">Head-to-Head Insights</div>
      {'<ul class="insight-list">' + safe_insights + '</ul>' if safe_insights else '<p class="commentary-text">No additional insights were returned.</p>'}
    </div>
    """,
    unsafe_allow_html=True,
  )

  commentary_text = result.get("commentary", "No commentary returned.")
  safe_commentary = html.escape(commentary_text)
  st.markdown(
    f"""
    <div class="section-card">
      <div class="section-heading">Commentary ({html.escape(language_label)})</div>
      <div class="commentary-text">{safe_commentary}</div>
    </div>
    """,
    unsafe_allow_html=True,
  )

  verdict_text = result.get("verdict", "No verdict returned.")
  safe_verdict = html.escape(str(verdict_text))
  st.markdown(
    f"""
    <div class="section-card">
      <div class="section-heading">Verdict</div>
      <div class="verdict-text">{safe_verdict}</div>
    </div>
    """,
    unsafe_allow_html=True,
  )

  winner = result.get("prediction", "Unknown")
  confidence = result.get("confidence", 0)
  safe_winner = html.escape(str(winner))
  safe_confidence = html.escape(str(confidence))
  winner_label = "Superior Bowler" if active_mode == "bowling" else "Predicted Winner"
  st.markdown(
    f"""
    <div class="section-card">
      <div class="summary-grid">
        <div class="summary-item">
          <div class="summary-label">{winner_label}</div>
          <div class="summary-value">{safe_winner}</div>
        </div>
        <div class="summary-item">
          <div class="summary-label">Confidence</div>
          <div class="summary-value">{safe_confidence}%</div>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
  )

  try:
    st.caption("Generating audio commentary...")
    audio_bytes = generate_tts_audio(commentary_text, selected_language)
    if audio_bytes:
      st.audio(audio_bytes, format="audio/mp3")
  except Exception as exc:
    st.warning(f"Could not generate commentary audio: {exc}")


