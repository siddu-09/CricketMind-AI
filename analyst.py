import os
import json
import re
import time
import requests
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# CricAPI config
CRICAPI_KEY = os.getenv("CRICAPI_KEY")
CRICAPI_BASE = "https://api.cricapi.com/v1"
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

SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "kn": "Kannada",
}

CACHE_TTL_SECONDS = int(os.getenv("PLAYER_STATS_CACHE_TTL", str(12 * 60 * 60)))
PLAYER_STATS_CACHE = {}
PLAYER_ID_CACHE = {}
API_BLOCKED_UNTIL = 0.0


def _cache_key(player_name):
    return str(player_name or "").strip().lower()


def _read_cached_stats(player_name, allow_stale=False):
    entry = PLAYER_STATS_CACHE.get(_cache_key(player_name))
    if not entry:
        return None
    age = time.time() - float(entry.get("cached_at", 0.0))
    if not allow_stale and age > CACHE_TTL_SECONDS:
        return None
    return dict(entry.get("data") or {})


def _write_cached_stats(player_name, data):
    if not player_name or not data:
        return
    PLAYER_STATS_CACHE[_cache_key(player_name)] = {
        "cached_at": time.time(),
        "data": dict(data),
    }


def _set_api_block_from_reason(reason):
    global API_BLOCKED_UNTIL
    text = str(reason or "").strip().lower()
    if not text:
        return

    minutes_match = re.search(r"(\d+)\s*minute", text)
    if minutes_match:
        wait_seconds = int(minutes_match.group(1)) * 60
        API_BLOCKED_UNTIL = max(API_BLOCKED_UNTIL, time.time() + wait_seconds)
        return

    if "hits today exceeded hits limit" in text:
        API_BLOCKED_UNTIL = max(API_BLOCKED_UNTIL, time.time() + 60 * 60)


def _is_temporarily_blocked():
    return time.time() < API_BLOCKED_UNTIL


def resolve_player_alias(name):
    clean_name = str(name or "").strip().lower()
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

    return str(name or "").strip().title()


def word_count(text):
    return len([w for w in str(text or "").strip().split() if w])


def to_number(value):
    try:
        cleaned = str(value).replace(",", "").strip()
        if cleaned in {"", "-", "N/A", "na", "none"}:
            return 0.0
        return float(cleaned)
    except Exception:
        return 0.0


def format_metric(value, decimals=2):
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.{decimals}f}"


def build_minimum_commentary(player1, player2, p1_data, p2_data, language_code="en"):
    english = (
        f"What a fascinating comparison between {player1} and {player2}. "
        f"{player1} currently has {p1_data.get('runs', 'N/A')} runs, an average of {p1_data.get('average', 'N/A')}, "
        f"and a strike rate of {p1_data.get('strike_rate', 'N/A')}. "
        f"On the other side, {player2} brings {p2_data.get('runs', 'N/A')} runs, an average of {p2_data.get('average', 'N/A')}, "
        f"and a strike rate of {p2_data.get('strike_rate', 'N/A')}. "
        "Both players show strong batting quality in this format, and the difference comes down to consistency, scoring pace, "
        "and match impact. This is a close contest with high quality on display from both stars."
    )

    hindi = (
        f"{player1} aur {player2} ke beech yeh tulna kaafi romanchak hai. "
        f"{player1} ke paas abhi {p1_data.get('runs', 'N/A')} runs hain, average {p1_data.get('average', 'N/A')} hai, "
        f"aur strike rate {p1_data.get('strike_rate', 'N/A')} hai. "
        f"Dusri taraf {player2} ke paas {p2_data.get('runs', 'N/A')} runs, average {p2_data.get('average', 'N/A')} "
        f"aur strike rate {p2_data.get('strike_rate', 'N/A')} hai. "
        "Dono players ki batting quality strong hai, aur antar consistency, scoring pace aur match impact par depend karta hai. "
        "Yeh mukabla kaafi close hai aur dono taraf se high quality performance dekhne ko milti hai."
    )

    kannada = (
        f"{player1} mattu {player2} madhye idu tumba interesting comparison agide. "
        f"{player1} hatra {p1_data.get('runs', 'N/A')} runs ide, average {p1_data.get('average', 'N/A')} ide, "
        f"mattu strike rate {p1_data.get('strike_rate', 'N/A')} ide. "
        f"Innondu kade {player2} hatra {p2_data.get('runs', 'N/A')} runs, average {p2_data.get('average', 'N/A')} "
        f"mattu strike rate {p2_data.get('strike_rate', 'N/A')} ide. "
        "Ibbara batting quality strong ide, mattu final vyatyasa consistency, scoring pace mattu match impact mele nirdharisuttade. "
        "Idu close contest, ibbaru players inda uttama performance nodalu sigutte."
    )

    templates = {
        "en": english,
        "hi": hindi,
        "kn": kannada,
    }
    return templates.get(language_code, english)


def ensure_commentary_language(commentary, language_code):
    text = str(commentary or "").strip()
    if not text:
        return ""
    if language_code == "en":
        return text

    target_language = SUPPORTED_LANGUAGES.get(language_code, "English")
    try:
        prompt = (
            f"Translate the following cricket commentary to {target_language}. "
            "Keep player names and numbers unchanged. Return only translated text, no extra notes.\n\n"
            f"Commentary:\n{text}"
        )
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
        )
        translated = str(response.choices[0].message.content or "").strip()
        return translated or text
    except Exception:
        return text

def get_player_stats(player_name):
    """
    Fetch player stats from CricAPI by player name.
    Returns dict with keys: runs, average, strike_rate, format_used, player_name.
    """
    if not CRICAPI_KEY:
        return None, "CRICAPI_KEY is missing"

    cached = _read_cached_stats(player_name, allow_stale=False)
    if cached:
        return cached, None

    if _is_temporarily_blocked():
        stale = _read_cached_stats(player_name, allow_stale=True)
        if stale:
            return stale, None
        wait_seconds = max(1, int(API_BLOCKED_UNTIL - time.time()))
        wait_minutes = (wait_seconds + 59) // 60
        return None, f"Blocked by CricAPI. Retry in about {wait_minutes} minute(s)."

    # Step 1: Search player
    search_url = f"{CRICAPI_BASE}/players"
    params = {"apikey": CRICAPI_KEY, "search": player_name}
    cached_player_id = PLAYER_ID_CACHE.get(_cache_key(player_name))
    player_id = cached_player_id
    resolved_name = player_name
    try:
        if not player_id:
            resp = requests.get(search_url, params=params, timeout=10)
            data = resp.json()
            if str(data.get("status", "")).lower() == "failure":
                reason = str(data.get("reason") or "Player search failed").strip()
                _set_api_block_from_reason(reason)
                stale = _read_cached_stats(player_name, allow_stale=True)
                if stale:
                    return stale, None
                return None, reason
            if not data.get("data"):
                stale = _read_cached_stats(player_name, allow_stale=True)
                if stale:
                    return stale, None
                return None, f"No player search results for '{player_name}'"
            players = data["data"]

            # Prefer exact name match when available, else first search hit.
            selected = next(
                (p for p in players if str(p.get("name", "")).strip().lower() == player_name.strip().lower()),
                players[0],
            )
            player_id = selected["id"]
            resolved_name = selected.get("name", player_name)
            PLAYER_ID_CACHE[_cache_key(player_name)] = player_id
    except Exception:
        return None, f"Failed to search player '{player_name}'"
    # Step 2: Get player details + stats
    stats_url = f"{CRICAPI_BASE}/players_info"
    params = {"apikey": CRICAPI_KEY, "id": player_id}
    try:
        resp = requests.get(stats_url, params=params, timeout=10)
        stats = resp.json()
        if stats.get("status") == "failure":
            reason = str(stats.get("reason") or "Player stats lookup failed").strip()
            _set_api_block_from_reason(reason)
            stale = _read_cached_stats(player_name, allow_stale=True)
            if stale:
                return stale, None
            return None, reason

        stat_rows = stats.get("data", {}).get("stats", [])
        if not stat_rows:
            return None, f"No stats returned for '{resolved_name}'"

        target_formats = ["odi", "t20i", "test"]
        batting_by_format = {}

        for fmt in target_formats:
            current = {
                row.get("stat"): row.get("value")
                for row in stat_rows
                if row.get("fn") == "batting" and str(row.get("matchtype", "")).lower() == fmt
            }
            if current:
                batting_by_format[fmt] = current

        if not batting_by_format:
            return None, f"No batting stats in ODI/T20I/Test for '{resolved_name}'"

        total_runs = 0.0
        weighted_avg_sum = 0.0
        weighted_sr_sum = 0.0
        total_innings = 0.0

        avg_values = []
        sr_values = []

        format_breakdown = {}
        for fmt, batting in batting_by_format.items():
            runs = to_number(batting.get("runs"))
            avg = to_number(batting.get("avg"))
            sr = to_number(batting.get("sr"))
            innings = to_number(batting.get("innings"))

            total_runs += runs

            if innings > 0:
                weighted_avg_sum += avg * innings
                weighted_sr_sum += sr * innings
                total_innings += innings

            if avg > 0:
                avg_values.append(avg)
            if sr > 0:
                sr_values.append(sr)

            format_breakdown[fmt] = {
                "runs": format_metric(runs, 0),
                "average": format_metric(avg),
                "strike_rate": format_metric(sr),
                "innings": format_metric(innings, 0),
            }

        if total_innings > 0:
            combined_avg = weighted_avg_sum / total_innings
            combined_sr = weighted_sr_sum / total_innings
        else:
            combined_avg = sum(avg_values) / len(avg_values) if avg_values else 0.0
            combined_sr = sum(sr_values) / len(sr_values) if sr_values else 0.0

        selected_format = "+".join([fmt.upper() for fmt in target_formats if fmt in batting_by_format])

        result = {
            "runs": format_metric(total_runs, 0),
            "average": format_metric(combined_avg),
            "strike_rate": format_metric(combined_sr),
            "format_used": selected_format,
            "player_name": resolved_name,
            "format_breakdown": format_breakdown,
        }
        _write_cached_stats(player_name, result)
        _write_cached_stats(resolved_name, result)
        return result, None
    except Exception:
        return None, f"Failed to fetch stats for '{player_name}'"


def cricket_analyst(player1, player2, language="en"):
    language_code = (language or "en").strip().lower()
    if language_code not in SUPPORTED_LANGUAGES:
        language_code = "en"

    player1 = resolve_player_alias(player1)
    player2 = resolve_player_alias(player2)

    # Fetch player stats from CricAPI
    p1_data, p1_error = get_player_stats(player1)
    p2_data, p2_error = get_player_stats(player2)
    if not p1_data or not p2_data:
        error_parts = []
        if not p1_data:
            error_parts.append(f"{player1}: {p1_error or 'player not found'}")
        if not p2_data:
            error_parts.append(f"{player2}: {p2_error or 'player not found'}")
        return {
            "status": "error",
            "message": "CricAPI lookup failed. " + " | ".join(error_parts)
        }

    # Prepare data for LLM prompt
    prompt = f"""
You are BOTH:
1. A cricket analyst (data-driven)
2. A cricket commentator (expressive)

Use this data:
{player1}: {p1_data}\n{player2}: {p2_data}

Note: runs/average/strike_rate are combined from ODI, T20I, and Test formats.

STRICT RULES:
- Use ONLY the given data
- Do NOT add external knowledge
- Return ONLY valid JSON
- No markdown or extra text

FORMAT:
{{
    "format_used": {{
        "player1": "",
        "player2": ""
    }},
  "analysis": {{
    "player1": {{
      "runs": "",
      "average": "",
      "strike_rate": "",
      "strength": ""
    }},
    "player2": {{
      "runs": "",
      "average": "",
      "strike_rate": "",
      "strength": ""
    }}
  }},
  "comparison": ["", "", ""],
  "commentary": "",
  "verdict": "",
  "prediction": "",
  "confidence": ""
}}
IMPORTANT:
- Prediction must be one player name
- Confidence must be percentage (0–100%)
- Keep "commentary" in {SUPPORTED_LANGUAGES[language_code]}
- "commentary" must be at least 50 words

Compare these two players:
{player1} vs {player2}
"""

    try:
        # Call Groq API
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )

        output = response.choices[0].message.content.strip()

        # Clean markdown if AI adds it
        if "```" in output:
            output = output.replace("```json", "").replace("```", "").strip()

        # Convert to JSON
        parsed_output = json.loads(output)

        # Decide winner using logic (NOT AI)
        try:
            avg1 = float(p1_data["average"]) if p1_data["average"] != "N/A" else 0
            avg2 = float(p2_data["average"]) if p2_data["average"] != "N/A" else 0
        except Exception:
            avg1 = avg2 = 0
        if avg1 > avg2:
            winner = player1
        else:
            winner = player2

        diff = abs(avg1 - avg2)
        if diff > 10:
            confidence = 90
        elif diff > 5:
            confidence = 75
        else:
            confidence = 60

        parsed_output["prediction"] = winner
        parsed_output["confidence"] = confidence
        parsed_output["format_used"] = {
            "player1": p1_data.get("format_used", "unknown"),
            "player2": p2_data.get("format_used", "unknown"),
        }

        commentary = str(parsed_output.get("commentary", "")).strip()
        if word_count(commentary) < 50:
            commentary = build_minimum_commentary(player1, player2, p1_data, p2_data, language_code)

        parsed_output["commentary"] = ensure_commentary_language(commentary, language_code)

        return parsed_output

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }