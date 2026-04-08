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

## Live Demo

- Hugging Face Space: https://huggingface.co/spaces/siddu9/cricketmind-ai

CricketMind AI is a player-vs-player cricket comparison app that combines live stats, AI analysis, and spoken commentary.

You can compare two cricketers using text input, view a stat-driven comparison dashboard, and listen to generated commentary in multiple languages.

## Project Description

The project has two main parts:

1. Backend API (FastAPI)

- Accepts two player names and selected commentary language.
- Fetches player statistics from CricAPI.
- Uses an LLM to generate structured analysis, comparison points, commentary, verdict, and prediction.
- Ensures commentary is meaningful (minimum length handling).
- Returns JSON response to the UI.

2. Frontend UI (Streamlit)

- Provides player input via text.
- Supports nickname/tagline resolution (for example: "King", "Hitman", "Thala").
- Sends requests to backend and renders cards, radar chart, insights, verdict, and confidence.
- Generates and auto-plays text-to-speech commentary.
- Supports commentary language selection: English, Hindi, Kannada.

## Models and AI Services Used

1. LLM for cricket analysis and commentary

- Provider: Groq
- Model: llama-3.3-70b-versatile
- Usage: Generates structured cricket comparison output in JSON format.

2. Text-to-Speech (TTS)

- Engine: Google Text-to-Speech (gTTS)
- Usage: Converts generated AI commentary to MP3 audio for playback.

3. Speech-to-Text (STT)

- Engine: Groq Whisper (whisper-large-v3-turbo)
- Usage: Transcribes spoken player names for accurate voice input and extraction.

4. External Cricket Data Source

- API: CricAPI
- Usage: Fetches player profile and batting stats used as analysis input.

## Tech Stack

- Python 3.13+
- FastAPI
- Streamlit
- Groq Python SDK
- requests
- matplotlib
- numpy
- gTTS
- python-dotenv

## Repository Structure

- app.py: FastAPI server and analyze endpoint
- analyst.py: Data fetch + LLM orchestration + response shaping
- ui.py: Streamlit dashboard, TTS playback, visualizations
- stt.py: Whisper STT transcription + robust player-name extraction helpers
- voice.py: Standalone voice interaction script using Whisper STT
- requirements.txt: Python dependencies

## Setup Instructions

1. Clone and enter project

```bash
git clone <your-repo-url>
cd cricketmind-source
```

2. Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Configure environment variables
   Create a .env file in project root:

```env
GROQ_API_KEY=your_groq_api_key
CRICAPI_KEY=your_cricapi_key
```

## Run the Project

1. Start backend API

```bash
uvicorn app:app --reload
```

2. Start Streamlit UI (new terminal)

```bash
streamlit run ui.py
```

3. Open app

- Streamlit UI: http://localhost:8501
- API health route: http://127.0.0.1:8000/

## Current Features

- Compare two cricket players with live stats.
- Radar chart for quick visual comparison.
- AI-generated head-to-head insights.
- AI commentary with minimum-length handling.
- TTS playback in English, Hindi, Kannada.
- Whisper-based voice input for player-name detection.
- Nickname and tagline mapping (for example: King -> Virat Kohli, Hitman -> Rohit Sharma).

## Notes

- TTS depends on Google services availability and internet connection.
- STT depends on GROQ_API_KEY and internet connectivity for Whisper transcription.
- Player matching quality depends on CricAPI search results.
- Nickname mapping can be extended in code for additional players.

## Deploy on Hugging Face Spaces

This project is configured for Hugging Face Docker Spaces.

### Files Used for Deployment

- Dockerfile: Builds the app container
- start.sh: Starts FastAPI backend (port 8000) + Streamlit UI (port 8501)
- .dockerignore: Excludes local/secret files from Docker build context

### Steps

1. Create a new Space on Hugging Face

- Space type: Docker
- Visibility: your choice (public/private)

2. Push this repository to the Space

- Add Space remote and push your code, or upload all files via the Space UI.

3. Add required Secrets in Space Settings

- GROQ_API_KEY
- CRICAPI_KEY

4. Wait for build and startup

- Hugging Face will build the Docker image using Dockerfile.
- The app is served through Streamlit on port 8501.

### Deploy Using Git (Example)

```bash
git init
git add .
git commit -m "Deploy CricketMind AI to Hugging Face Spaces"
git remote add space https://huggingface.co/spaces/<username>/<space-name>
git push --force space main
```

### Important Runtime Notes

- Keep BACKEND_URL as default (http://127.0.0.1:8000/analyze) for Docker Space runtime.
- If TTS audio generation is slow, retry after a few seconds.
