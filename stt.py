import io
import os
import re
from difflib import SequenceMatcher

from dotenv import load_dotenv
from groq import Groq


load_dotenv()

_CLIENT = None

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


def _normalize(text):
    cleaned = re.sub(r"[^a-z0-9\s]", " ", str(text or "").lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def _get_client():
    global _CLIENT
    if _CLIENT is not None:
        return _CLIENT

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None

    _CLIENT = Groq(api_key=api_key)
    return _CLIENT


def transcribe_wav_bytes(audio_bytes, language="en"):
    if not audio_bytes:
        return "", "Audio is empty."

    client = _get_client()
    if client is None:
        return "", "GROQ_API_KEY is missing. Please set it in your environment."

    buffer = io.BytesIO(audio_bytes)
    buffer.name = "speech.wav"

    try:
        result = client.audio.transcriptions.create(
            file=buffer,
            model="whisper-large-v3-turbo",
            language=(language or "en").lower(),
            temperature=0,
            prompt=(
                "This is cricket context. Player names may include Virat Kohli, "
                "Rohit Sharma, MS Dhoni, KL Rahul, Hardik Pandya, Jasprit Bumrah, "
                "Mohammed Siraj, Sachin Tendulkar."
            ),
        )
    except Exception as exc:
        return "", f"Whisper transcription failed: {exc}"

    transcript = str(getattr(result, "text", "") or "").strip()
    if not transcript:
        return "", "No speech detected from audio."
    return transcript, ""


def _match_player_name(fragment):
    normalized = _normalize(fragment)
    if not normalized:
        return ""

    if normalized in COMMON_PLAYER_ALIASES:
        return COMMON_PLAYER_ALIASES[normalized]

    # Prefer longest direct phrase match in the spoken fragment.
    for alias in sorted(COMMON_PLAYER_ALIASES, key=len, reverse=True):
        if alias in normalized:
            return COMMON_PLAYER_ALIASES[alias]

    best_alias = ""
    best_score = 0.0
    for alias in COMMON_PLAYER_ALIASES:
        score = SequenceMatcher(a=normalized, b=alias).ratio()
        if score > best_score:
            best_score = score
            best_alias = alias

    if best_alias and best_score >= 0.78:
        return COMMON_PLAYER_ALIASES[best_alias]

    return normalized.title()


def extract_players_from_transcript(text):
    normalized = _normalize(text)
    if not normalized:
        return None, None

    normalized = re.sub(r"\b(versus|vs|against|and|with|or)\b", " vs ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()

    parts = [part.strip() for part in normalized.split(" vs ") if part.strip()]

    if len(parts) >= 2:
        player1 = _match_player_name(parts[0])
        player2 = _match_player_name(parts[1])
        if player1 and player2 and player1.lower() != player2.lower():
            return player1, player2

    # Fallback: detect first two unique aliases appearing anywhere in transcript.
    found = []
    for alias in sorted(COMMON_PLAYER_ALIASES, key=len, reverse=True):
        if alias in normalized:
            canonical = COMMON_PLAYER_ALIASES[alias]
            if canonical not in found:
                found.append(canonical)
            if len(found) == 2:
                return found[0], found[1]

    return None, None
