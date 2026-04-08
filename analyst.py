import os
import json
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


def word_count(text):
    return len([w for w in str(text or "").strip().split() if w])


def build_minimum_commentary(player1, player2, p1_data, p2_data):
    return (
        f"What a fascinating comparison between {player1} and {player2}. "
        f"{player1} currently has {p1_data.get('runs', 'N/A')} runs, an average of {p1_data.get('average', 'N/A')}, "
        f"and a strike rate of {p1_data.get('strike_rate', 'N/A')}. "
        f"On the other side, {player2} brings {p2_data.get('runs', 'N/A')} runs, an average of {p2_data.get('average', 'N/A')}, "
        f"and a strike rate of {p2_data.get('strike_rate', 'N/A')}. "
        "Both players show strong batting quality in this format, and the difference comes down to consistency, scoring pace, "
        "and match impact. This is a close contest with high quality on display from both stars."
    )

def get_player_stats(player_name):
    """
    Fetch player stats from CricAPI by player name.
    Returns dict with keys: runs, average, strike_rate, format_used, player_name.
    """
    if not CRICAPI_KEY:
        return None
    # Step 1: Search player
    search_url = f"{CRICAPI_BASE}/players"
    params = {"apikey": CRICAPI_KEY, "search": player_name}
    try:
        resp = requests.get(search_url, params=params, timeout=10)
        data = resp.json()
        if not data.get("data"):
            return None
        players = data["data"]

        # Prefer exact name match when available, else first search hit.
        selected = next(
            (p for p in players if str(p.get("name", "")).strip().lower() == player_name.strip().lower()),
            players[0],
        )
        player_id = selected["id"]
        resolved_name = selected.get("name", player_name)
    except Exception:
        return None
    # Step 2: Get player details + stats
    stats_url = f"{CRICAPI_BASE}/players_info"
    params = {"apikey": CRICAPI_KEY, "id": player_id}
    try:
        resp = requests.get(stats_url, params=params, timeout=10)
        stats = resp.json()
        if stats.get("status") == "failure":
            return None

        stat_rows = stats.get("data", {}).get("stats", [])
        if not stat_rows:
            return None

        # Prefer ODI, then T20I, then Test, then first available batting format.
        preferred_formats = ["odi", "t20i", "test", "t20", "firstclass", "lista"]
        batting = {}
        selected_format = "unknown"

        for fmt in preferred_formats:
            current = {
                row.get("stat"): row.get("value")
                for row in stat_rows
                if row.get("fn") == "batting" and str(row.get("matchtype", "")).lower() == fmt
            }
            if current:
                batting = current
                selected_format = fmt
                break

        if not batting:
            batting = {
                row.get("stat"): row.get("value")
                for row in stat_rows
                if row.get("fn") == "batting"
            }
            if batting:
                selected_format = "batting_any"

        if not batting:
            return None

        return {
            "runs": batting.get("runs", "N/A"),
            "average": batting.get("avg", "N/A"),
            "strike_rate": batting.get("sr", "N/A"),
            "format_used": selected_format,
            "player_name": resolved_name,
        }
    except Exception:
        return None


def cricket_analyst(player1, player2, language="en"):
    supported_languages = {
        "en": "English",
        "hi": "Hindi",
        "kn": "Kannada",
    }
    language_code = (language or "en").strip().lower()
    if language_code not in supported_languages:
        language_code = "en"

    # Fetch player stats from CricAPI
    p1_data = get_player_stats(player1)
    p2_data = get_player_stats(player2)
    if not p1_data or not p2_data:
        return {
            "status": "error",
            "message": "One or both players not found via CricAPI"
        }

    # Prepare data for LLM prompt
    prompt = f"""
You are BOTH:
1. A cricket analyst (data-driven)
2. A cricket commentator (expressive)

Use this data:
{player1}: {p1_data}\n{player2}: {p2_data}

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
- Keep "commentary" in {supported_languages[language_code]}
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
            parsed_output["commentary"] = build_minimum_commentary(player1, player2, p1_data, p2_data)

        return parsed_output

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }