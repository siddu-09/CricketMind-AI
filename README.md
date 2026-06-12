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

- Compare any two players with one click.
- Show runs, average, strike rate, and a bar-chart comparison.
- Generate AI commentary, verdict, and winner confidence.
- Support voice input for player names.
- Read out commentary with text-to-speech.
- Support commentary in English, Hindi, and Kannada.

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
