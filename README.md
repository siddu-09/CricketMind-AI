---
title: CricketMind AI
emoji: "🏏"
colorFrom: green
colorTo: yellow
sdk: docker
app_port: 8501
pinned: false
---

# CricketMind AI

CricketMind AI helps you compare two cricket players using live stats, AI analysis, and voice-assisted input.

Live demo: https://huggingface.co/spaces/siddu9/cricketmind-ai

## What This App Does

- **Live player comparison** — Fetch real-time stats (runs, average, strike rate, wickets, economy) for any two players across ODI, T20I, Test, and IPL formats via CricAPI.
- **AI-driven insights** — LLaMA 3.3 70B generates structured commentary, comparison points, verdict, and a prediction grounded in the actual stats.
- **Confidence score** — Python-calculated score (60 / 75 / 90%) based on the gap between players' averages, not LLM-guessed, so it's always consistent.
- **Format filter** — Filter the entire comparison (stats + chart + commentary) to a specific format: ODI, T20I, Test, IPL, or all combined.
- **Batting / Bowling mode** — Switch between batter metrics (runs, average, strike rate) and bowler metrics (wickets, economy, bowling average).
- **Radar chart visualisation** — Spider chart per format tab showing normalised stat comparison across multiple axes at once.
- **Deep-dive splits** — Venue (Home/Away/Neutral), opposition, situational (chasing vs setting, pace vs spin), and career timeline breakdowns.
- **Voice input (STT)** — Speak two player names; Whisper Large v3 Turbo transcribes them and fuzzy alias resolution maps nicknames to canonical names.
- **Audio commentary (TTS)** — Google gTTS reads the AI commentary aloud in English, Hindi, or Kannada.
- **Multilingual output** — Commentary written in native Devanagari (Hindi) or Kannada script, not romanised transliteration.
- **12-hour stats cache** — CricAPI responses cached in memory; stale cache served as fallback when API rate limit is hit.

## Screenshots

### 1) Home and Voice Input

![CricketMind AI Home](assets/screenshots/home-top.png)

### 2) Comparison Output

![CricketMind AI Comparison](assets/screenshots/after-compare.png)

### 3) Stats and Chart Section

![CricketMind AI Stats and Chart](assets/screenshots/stats-section.png)

## How It Works

1. You enter or speak two player names.
2. The backend fetches player data from CricAPI.
3. The LLM builds a structured analysis and commentary.
4. The UI renders stats, charts, insights, and verdict.
5. TTS generates playable audio commentary.

## Tech Stack

- Python 3.13+
- FastAPI
- Streamlit
- Groq SDK
- gTTS
- matplotlib
- numpy
- requests
- python-dotenv

## Key Technologies Explained

### FastAPI
A modern Python web framework used to build the backend REST API (`/analyze` endpoint).
- **Why FastAPI over Flask / Django?** FastAPI is the fastest Python API framework, natively supports async requests (important when waiting for CricAPI + Groq simultaneously), and auto-generates interactive API docs at `/docs` with zero extra code.

| Framework | Speed | Async | Auto Docs |
|---|---|---|---|
| **FastAPI** ✅ | ⚡ Fastest | ✅ Native | ✅ Auto |
| Flask | Medium | ❌ Limited | ❌ Manual |
| Django | Slower | ❌ Limited | ❌ Manual |

---

### CricAPI
A third-party REST API that provides live cricket player statistics — runs, average, strike rate, wickets, economy across ODI/T20I/Test/IPL.
- Without this, you would have to scrape ESPN Cricinfo manually, which is unreliable and violates terms of service.
- Both players are fetched **in parallel** using Python's `ThreadPoolExecutor`, halving the wait time.

| Source | Free Tier | Official API | All Formats |
|---|---|---|---|
| **CricAPI** ✅ | ✅ | ✅ | ✅ |
| ESPN Cricinfo | ❌ | ❌ Scraping | Manual |
| Cricbuzz | ❌ | ❌ Unofficial | Unreliable |
| Sportmonks | ✅ | ✅ | ✅ but expensive |

---

### Groq
A company that runs AI models on custom **LPU (Language Processing Unit)** chips. Groq does not build models — they host Meta's LLaMA and OpenAI's Whisper at extremely high inference speed (~300 tokens/sec for LLaMA 3.3 70B, vs ~30 for GPT-4o). Both the LLM and STT in this project run on Groq using the same single API key.

---

### Streamlit
A Python library that turns Python scripts into interactive web apps with no HTML or JavaScript needed. Chosen because the entire project is Python — no need for a separate React or Vue frontend.

| Tool | Language | Setup | Best For |
|---|---|---|---|
| **Streamlit** ✅ | Python | Zero config | AI/data apps |
| React | JavaScript | Complex | General web |
| Gradio | Python | Zero config | Model demos only |
| Dash | Python | Medium | Data dashboards |

## AI Model

### Model Used: Meta LLaMA 3.3 70B Versatile (via Groq)

This project uses **LLaMA 3.3 70B Versatile**, an open-source large language model created by **Meta AI**, accessed through the **Groq API** for ultra-fast inference.

```
Model  : llama-3.3-70b-versatile
Creator: Meta AI
Host   : Groq (LPU inference engine)
```

**Meta** built and trained the model. **Groq** runs it on custom LPU (Language Processing Unit) hardware, delivering speeds of ~300 tokens/second — roughly 10x faster than GPT-4o.

---

### Why LLaMA 3.3 70B Versatile?

| Model | Speed on Groq | Quality | Cost | Multilingual | Open Source |
|---|---|---|---|---|---|
| **LLaMA 3.3 70B Versatile** ✅ | ⚡ ~300 tok/s | ★★★★★ | Free tier | ✅ Strong | ✅ |
| LLaMA 3.1 8B | ⚡⚡ Very fast | ★★★☆☆ | Free | ⚠️ Weak | ✅ |
| GPT-4o (OpenAI) | 🐢 Moderate | ★★★★★ | 💰 Paid | ✅ | ❌ |
| Claude 3.5 Sonnet | 🐢 Moderate | ★★★★★ | 💰 Paid | ✅ | ❌ |
| Gemini 1.5 Pro | 🐢 Moderate | ★★★★☆ | 💰 Paid | ✅ | ❌ |
| Mixtral 8x7B | ⚡ Fast | ★★★☆☆ | Free | ⚠️ Weak | ✅ |

**Key reasons this model was chosen for CricketMind AI:**

1. **Multilingual output** — Reliably writes native Hindi (Devanagari) and Kannada script for commentary. Smaller 8B models often romanize non-English languages incorrectly.

2. **Speed via Groq** — Real-time sports commentary needs fast responses. Groq's LPU delivers ~300 tokens/second on this model, making commentary feel instant.

3. **Free / low cost** — Groq offers a generous free tier. Paid alternatives like GPT-4o or Claude cost significantly more per token, making them impractical for hobby/student projects.

4. **Reliable structured JSON output** — The app relies on the LLM returning strict JSON (analysis, comparison, verdict, commentary). At 70B parameters, this model handles it consistently without breaking format.

5. **90% of GPT-4o quality at 0% cost** — The 70B size gives strong reasoning and language quality that matches or exceeds GPT-3.5, and approaches GPT-4o for tasks like sports analysis and commentary generation.

---

## Speech-to-Text (STT)

### Model Used: OpenAI Whisper Large v3 Turbo (via Groq)

Voice input is transcribed using **Whisper Large v3 Turbo**, an open-source speech recognition model created by **OpenAI**, served through the **Groq API**.

```
Model  : whisper-large-v3-turbo
Creator: OpenAI (open-sourced)
Host   : Groq API
```

### Why Whisper Large v3 Turbo?

| Model | Speed | Accuracy | Timeout Risk | Best For |
|---|---|---|---|---|
| **Whisper Large v3 Turbo** ✅ | ⚡ Very fast | ★★★★☆ | Very low | Short voice clips |
| Whisper Large v3 | 🐢 Slow | ★★★★★ | High | Long audio files |
| Whisper Small / Base | ⚡⚡ Fastest | ★★☆☆☆ | Very low | Simple commands only |

**Key reasons Whisper Large v3 Turbo was chosen:**

1. **Perfect for short voice input** — Users speak just two player names (2–5 seconds). The turbo variant is optimally sized for this — full `large-v3` is overkill and risks timeouts on slow networks.

2. **Cricket name accuracy** — At the large-v3 quality level, it correctly recognises difficult cricket player names (e.g., Jasprit Bumrah, Yuzvendra Chahal, Kagiso Rabada) that smaller models misfire on.

3. **Fastest inference via Groq** — Groq's LPU hardware runs Whisper turbo extremely fast, so voice-to-text feels near-instant even for users on slower connections.

4. **Same API key, zero extra cost** — Groq's Whisper endpoint uses the same `GROQ_API_KEY` as the LLM, meaning no additional setup or billing account is needed.

---

## Text-to-Speech (TTS)

### Model Used: Google gTTS (Google Text-to-Speech)

Audio commentary playback uses **gTTS**, a Python wrapper around Google's Text-to-Speech API.

```
Library : gTTS (pip install gtts)
Provider: Google Translate TTS (no API key required)
```

### Why Google gTTS?

| Provider | Hindi | Kannada | Cost | Setup | Voice Quality |
|---|---|---|---|---|---|
| **Google gTTS** ✅ | ✅ Native | ✅ Native | 🆓 Free | Zero config | Natural |
| ElevenLabs | ✅ | ❌ | 💰 Paid | API key | Best |
| AWS Polly | ✅ | ⚠️ Limited | 💰 Paid | AWS account | Very good |
| Coqui TTS | ⚠️ | ❌ | 🆓 Free | Model download | Robotic |
| pyttsx3 | ⚠️ | ❌ | 🆓 Free | Zero config | Robotic |

**Key reasons gTTS was chosen:**

1. **Only free TTS with full Hindi + Kannada support** — This project generates commentary in English, Hindi, and Kannada. gTTS is the only free option that natively supports all three with natural pronunciation.

2. **Zero configuration** — No API key, no cloud account, no model download. Just `pip install gtts` and it works out of the box.

3. **Natural voice quality** — Google's TTS engine produces human-sounding speech, unlike offline engines (pyttsx3, Coqui) which sound robotic.

4. **Lightweight** — gTTS is a tiny library with no heavy dependencies, keeping the Docker image and startup time small.

## Key Features in Detail

### Confidence Score
Calculated in Python from the gap between the two players' key stats — **not** generated by the LLM, so it is always consistent and grounded in real data.

- **Batting mode** (based on batting average gap):
  - Gap > 10 → **90%** confidence (clear winner)
  - Gap 5–10 → **75%** confidence (moderate lead)
  - Gap < 5 → **60%** confidence (very close)
- **Bowling mode** (based on bowling average gap — lower is better):
  - Gap > 5 → **90%** | Gap 2–5 → **75%** | Gap < 2 → **60%**

The LLM is asked for a `confidence` field in its JSON prompt, but after parsing, the Python-calculated value always overwrites it.

---

### Format Filter
Selecting ODI / T20I / Test / IPL sends the format to the backend. The backend then:
1. Pulls that format's specific stats from the format breakdown
2. Passes those stats to the LLM prompt
3. LLM commentary, verdict, and confidence score all reflect the chosen format
4. The radar chart and stats breakdown tabs switch to show only that format's data

---

### Deep Dive Splits
Because raw career averages don't tell the full story, the app generates detailed performance splits:

| Split Type | What It Shows |
|---|---|
| **Venue splits** | Home / Away / Neutral average and strike rate |
| **Opposition splits** | Performance vs Australia, England, India/Pakistan, South Africa, New Zealand |
| **Situational** | Chasing vs Setting a target; vs Pace bowling vs Spin bowling |
| **Career Timeline** | Year-by-year average trend from 2018 to 2025 |

These splits are **deterministically generated** from the player's real career average using a SHA-256 seeded random function — same player always gives the same splits, making results consistent without needing ball-by-ball historical data.

---

### 12-Hour Stats Cache + Rate-Limit Fallback
- Player stats from CricAPI are stored in memory for 12 hours after the first fetch.
- If 100 users compare the same two players, CricAPI is called only once — not 100 times.
- When CricAPI blocks requests (free-tier daily limit hit), the app detects the block from the error message, parses the retry wait time, and **serves the last cached stats** instead of showing an error.

---

### Player Alias Resolution
Users can type nicknames or voice-speak partial names. A 4-stage pipeline maps them to canonical CricAPI names:

1. **Exact match** — `"Virat Kohli"` → `"Virat Kohli"`
2. **Substring match** — `"kohli"` → `"Virat Kohli"`
3. **Fuzzy match** — `"virt kohly"` → `"Virat Kohli"` (SequenceMatcher similarity)
4. **Alias dictionary** — `"king kohli"`, `"hitman"`, `"God of cricket"` → mapped via `players.json`

---

### Multilingual Commentary Pipeline

```
User selects language (e.g. Kannada)
    → LLM prompt instructs: "write in Kannada native script"
    → Response validated for Kannada Unicode block (U+0C80–U+0CFF)
    → If romanised text returned → automatic retry with stronger instruction
    → gTTS converts Kannada text → Kannada audio
    → User hears native Kannada cricket commentary
```

---

## Project Structure

- app.py: FastAPI app and analyze endpoint
- analyst.py: data fetch and LLM orchestration
- ui.py: Streamlit frontend and visualization
- stt.py: speech-to-text and player extraction logic
- voice.py: standalone voice interaction script
- requirements.txt: Python dependencies
- start.sh: starts backend and frontend in Docker runtime
- Dockerfile: image build for deployment

## Quick Start (Local)

1. Clone the repo and open it.

2. Create and activate virtual environment.

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies.

```bash
pip install -r requirements.txt
```

4. Create .env file in project root.

```env
GROQ_API_KEY=your_groq_api_key
CRICAPI_KEY=your_cricapi_key
```

5. Start backend API.

```bash
uvicorn app:app --reload
```

6. Start Streamlit in a new terminal.

```bash
streamlit run ui.py
```

7. Open the app.

- UI: http://localhost:8501
- API health check: http://127.0.0.1:8000/

## Deployment (Hugging Face Spaces)

This repo is configured for Docker Spaces.

1. Create a new Hugging Face Space with Docker SDK.
2. Add secrets in Space settings.
   - GROQ_API_KEY
   - CRICAPI_KEY
3. Push this repo to your Space remote.
4. Wait for the build to complete.

## Notes

- Voice transcription quality depends on microphone quality and network stability.
- STT requires valid Groq API credentials.
- Player matching can be improved over time by extending aliases in stt.py.
