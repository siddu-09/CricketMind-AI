import io
import os
import re

from dotenv import load_dotenv
from groq import Groq

# F1: import everything from the single centralised registry
from players import COMMON_PLAYER_ALIASES, _match_player_name, extract_players_from_transcript  # noqa: F401

load_dotenv()

_CLIENT = None
_TRANSCRIPTION_MODELS = [
    "whisper-large-v3-turbo",
    "whisper-large-v3",
    "distil-whisper-large-v3-en",
]


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


def _guess_audio_extension(audio_bytes, filename="", mime_type=""):
    file_hint = str(filename or "").strip().lower()
    if "." in file_hint:
        ext = file_hint.rsplit(".", 1)[-1]
        if ext in {"wav", "mp3", "m4a", "ogg", "webm", "flac", "mpga", "mpeg"}:
            return ext

    mime_hint = str(mime_type or "").strip().lower()
    if "/" in mime_hint:
        subtype = mime_hint.split("/")[-1].split(";")[0].strip()
        if subtype in {"wav", "x-wav", "mpeg", "mp3", "m4a", "ogg", "webm", "flac", "mpga"}:
            return "wav" if subtype == "x-wav" else ("mp3" if subtype == "mpeg" else subtype)

    header = bytes(audio_bytes[:16])
    if header.startswith(b"RIFF") and b"WAVE" in header:
        return "wav"
    if header.startswith(b"OggS"):
        return "ogg"
    if header.startswith(b"ID3") or (len(header) >= 2 and header[0] == 0xFF and (header[1] & 0xE0) == 0xE0):
        return "mp3"
    if header.startswith(b"fLaC"):
        return "flac"
    if header.startswith(b"\x1A\x45\xDF\xA3"):
        return "webm"
    if len(header) >= 8 and header[4:8] == b"ftyp":
        return "m4a"
    return "wav"


def transcribe_wav_bytes(audio_bytes, language="en", filename="", mime_type=""):
    if not audio_bytes:
        return "", "Audio is empty."

    client = _get_client()
    if client is None:
        return "", "GROQ_API_KEY is missing. Please set it in your environment."

    ext = _guess_audio_extension(audio_bytes, filename=filename, mime_type=mime_type)
    lang = str(language or "").strip().lower()

    last_error = ""
    for model_name in _TRANSCRIPTION_MODELS:
        buffer = io.BytesIO(audio_bytes)
        buffer.name = f"speech.{ext}"
        request_args = {
            "file": buffer,
            "model": model_name,
            "temperature": 0,
            "prompt": (
                "Cricket context. Player names can include Virat Kohli, Rohit Sharma, "
                "MS Dhoni, KL Rahul, Hardik Pandya, Jasprit Bumrah, Mohammed Siraj, "
                "Sachin Tendulkar, Babar Azam, Pat Cummins, Ben Stokes. Return clear text."
            ),
        }
        if lang:
            request_args["language"] = lang

        try:
            result = client.audio.transcriptions.create(**request_args)
            transcript = str(getattr(result, "text", "") or "").strip()
            if transcript:
                return transcript, ""
            last_error = "No speech detected from audio."
        except Exception as exc:
            last_error = str(exc)

    if not last_error:
        last_error = "Unknown transcription error."
    return "", f"Whisper transcription failed: {last_error}"


# extract_players_from_transcript is imported directly from players.py above.
# It is re-exported here so existing callers (ui.py) can keep using:
#   from stt import transcribe_wav_bytes, extract_players_from_transcript