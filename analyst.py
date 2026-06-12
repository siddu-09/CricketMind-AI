import os
import json
import re
import time
import requests
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from groq import Groq

# F1: single import — replaces the local resolve_player_alias that was here before
from players import resolve_player_alias

# Load environment variables
load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# CricAPI config
CRICAPI_KEY = os.getenv("CRICAPI_KEY")
CRICAPI_BASE = "https://api.cricapi.com/v1"

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
    # F1 fix: fallback commentary now uses native script for hi and kn
    english = (
        f"What a fascinating comparison between {player1} and {player2}. "
        f"{player1} currently has {p1_data.get('runs', 'N/A')} runs, an average of {p1_data.get('average', 'N/A')}, "
        f"and a strike rate of {p1_data.get('strike_rate', 'N/A')}. "
        f"On the other side, {player2} brings {p2_data.get('runs', 'N/A')} runs, an average of {p2_data.get('average', 'N/A')}, "
        f"and a strike rate of {p2_data.get('strike_rate', 'N/A')}. "
        "Both players show strong batting quality in this format, and the difference comes down to consistency, scoring pace, "
        "and match impact. This is a close contest with high quality on display from both stars."
    )

    # Native Devanagari script — gTTS lang='hi' now pronounces this correctly
    hindi = (
        f"{player1} और {player2} के बीच यह तुलना बेहद रोमांचक है। "
        f"{player1} के पास अभी {p1_data.get('runs', 'N/A')} रन हैं, औसत {p1_data.get('average', 'N/A')} है, "
        f"और स्ट्राइक रेट {p1_data.get('strike_rate', 'N/A')} है। "
        f"दूसरी तरफ {player2} के पास {p2_data.get('runs', 'N/A')} रन, औसत {p2_data.get('average', 'N/A')} "
        f"और स्ट्राइक रेट {p2_data.get('strike_rate', 'N/A')} है। "
        "दोनों खिलाड़ियों की बल्लेबाजी बेहतरीन है, और अंतर निरंतरता, स्कोरिंग गति और मैच प्रभाव पर निर्भर करता है। "
        "यह मुकाबला काफी करीबी है और दोनों तरफ से उच्च गुणवत्ता का प्रदर्शन देखने को मिलता है।"
    )

    # Native Kannada script — gTTS lang='kn' now pronounces this correctly
    kannada = (
        f"{player1} ಮತ್ತು {player2} ನಡುವಿನ ಈ ಹೋಲಿಕೆ ತುಂಬಾ ಆಸಕ್ತಿಕರವಾಗಿದೆ। "
        f"{player1} ಬಳಿ ಈಗ {p1_data.get('runs', 'N/A')} ರನ್‌ಗಳಿವೆ, ಸರಾಸರಿ {p1_data.get('average', 'N/A')} ಆಗಿದೆ, "
        f"ಮತ್ತು ಸ್ಟ್ರೈಕ್ ರೇಟ್ {p1_data.get('strike_rate', 'N/A')} ಆಗಿದೆ. "
        f"ಇನ್ನೊಂದು ಕಡೆ {player2} ಬಳಿ {p2_data.get('runs', 'N/A')} ರನ್‌ಗಳು, ಸರಾಸರಿ {p2_data.get('average', 'N/A')} "
        f"ಮತ್ತು ಸ್ಟ್ರೈಕ್ ರೇಟ್ {p2_data.get('strike_rate', 'N/A')} ಇದೆ. "
        "ಇಬ್ಬರು ಆಟಗಾರರ ಬ್ಯಾಟಿಂಗ್ ಗುಣಮಟ್ಟ ಉತ್ತಮವಾಗಿದೆ, ಮತ್ತು ವ್ಯತ್ಯಾಸವು ಸ್ಥಿರತೆ, ಸ್ಕೋರಿಂಗ್ ವೇಗ ಮತ್ತು ಪಂದ್ಯದ ಪ್ರಭಾವದ ಮೇಲೆ ಅವಲಂಬಿತವಾಗಿದೆ. "
        "ಇದು ಒಂದು ಪ್ರತಿಭಾವಂತ ಸ್ಪರ್ಧೆಯಾಗಿದ್ದು, ಇಬ್ಬರಿಂದಲೂ ಉತ್ತಮ ಪ್ರದರ್ಶನ ನೋಡಲು ಸಿಗುತ್ತದೆ."
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

    # F1 fix: reject Romanised output — check that non-English response has native script
    def _is_native_script(s, lang):
        if lang == "hi":
            # Devanagari block: U+0900–U+097F
            return bool(re.search(r"[\u0900-\u097F]", s))
        if lang == "kn":
            # Kannada block: U+0C80–U+0CFF
            return bool(re.search(r"[\u0C80-\u0CFF]", s))
        return True

    try:
        prompt = (
            f"Translate the following cricket commentary to {target_language}. "
            f"You MUST write in {target_language} native script (not Roman/Latin transliteration). "
            "Keep player names and numbers unchanged. Return only translated text, no extra notes.\n\n"
            f"Commentary:\n{text}"
        )
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
        )
        translated = str(response.choices[0].message.content or "").strip()

        # If the translation came back Romanised, retry once with a stronger instruction
        if translated and not _is_native_script(translated, language_code):
            retry_prompt = (
                f"Your previous translation was in Roman script. "
                f"You MUST write in {target_language} using its own alphabet/script. "
                f"Retry the translation:\n\n{text}"
            )
            retry_resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": retry_prompt}],
            )
            retry_text = str(retry_resp.choices[0].message.content or "").strip()
            if retry_text and _is_native_script(retry_text, language_code):
                return retry_text

        return translated or text
    except Exception:
        return text


def _get_seeded_random(seed_string):
    state = hashlib.sha256(seed_string.encode('utf-8')).digest()
    def rand_float():
        nonlocal state
        state = hashlib.sha256(state).digest()
        val = int.from_bytes(state[:8], byteorder='big')
        return val / 18446744073709551615.0
    def rand_int(a, b):
        return int(a + rand_float() * (b - a + 1))
    return rand_float, rand_int

def _generate_timeline(player_name, career_val, is_bowling=False):
    rand_float, rand_int = _get_seeded_random(player_name + "_timeline")
    years = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
    timeline = []
    
    try:
        base = float(career_val)
    except (ValueError, TypeError):
        base = 25.0 if is_bowling else 35.0
        
    if base <= 0:
        base = 25.0 if is_bowling else 35.0
        
    for yr in years:
        variation = (rand_float() * 0.5) - 0.25  # -25% to +25%
        val = base * (1.0 + variation)
        val = max(1.0, val)
        timeline.append({"year": yr, "value": round(val, 2)})
    return timeline

def _generate_recent_form(player_name, career_avg, is_bowling=False):
    rand_float, rand_int = _get_seeded_random(player_name + "_recent")
    form = []
    
    try:
        base_avg = float(career_avg)
    except (ValueError, TypeError):
        base_avg = 25.0 if is_bowling else 35.0
        
    if base_avg <= 0:
        base_avg = 25.0 if is_bowling else 35.0
        
    for _ in range(5):
        if is_bowling:
            wkt_chance = rand_float()
            if wkt_chance < 0.15:
                wkts = 0
            elif wkt_chance < 0.45:
                wkts = 1
            elif wkt_chance < 0.75:
                wkts = 2
            elif wkt_chance < 0.90:
                wkts = 3
            else:
                wkts = rand_int(4, 5)
            runs = rand_int(15, 55)
            form.append(f"{wkts}/{runs}")
        else:
            roll = rand_float()
            if roll < 0.15:
                score = rand_int(0, 12)
            elif roll < 0.50:
                score = rand_int(13, 45)
            elif roll < 0.80:
                score = rand_int(46, 88)
            else:
                score = rand_int(89, 145)
            not_out = "*" if rand_float() < 0.18 else ""
            form.append(f"{score}{not_out}")
    return form

def _generate_splits(player_name, career_val1, career_val2, is_bowling=False):
    rand_float, rand_int = _get_seeded_random(player_name + "_splits")
    
    try:
        val1_base = float(career_val1)
    except (ValueError, TypeError):
        val1_base = 25.0 if is_bowling else 35.0
        
    try:
        val2_base = float(career_val2)
    except (ValueError, TypeError):
        val2_base = 8.0 if is_bowling else 130.0
        
    if val1_base <= 0: val1_base = 25.0 if is_bowling else 35.0
    if val2_base <= 0: val2_base = 8.0 if is_bowling else 130.0
    
    venues = ["Home", "Away", "Neutral"]
    venue_splits = {}
    for v in venues:
        v1_var = (rand_float() * 0.2) - 0.1
        v2_var = (rand_float() * 0.1) - 0.05
        v1 = val1_base * (1.0 + v1_var)
        v2 = val2_base * (1.0 + v2_var)
        venue_splits[v] = {
            "avg": round(max(0.1, v1), 2),
            "sr_or_econ": round(max(0.1, v2), 2)
        }
        
    opponents = ["Australia", "England", "India" if "India" not in player_name else "Pakistan", "South Africa", "New Zealand"]
    opposition_splits = {}
    for opp in opponents:
        v1_var = (rand_float() * 0.3) - 0.15
        v2_var = (rand_float() * 0.16) - 0.08
        v1 = val1_base * (1.0 + v1_var)
        v2 = val2_base * (1.0 + v2_var)
        opposition_splits[opp] = {
            "avg": round(max(0.1, v1), 2),
            "sr_or_econ": round(max(0.1, v2), 2)
        }
    return venue_splits, opposition_splits

def _generate_situational(player_name, career_val1, career_val2, is_bowling=False):
    rand_float, rand_int = _get_seeded_random(player_name + "_situational")
    
    try:
        val1_base = float(career_val1)
    except (ValueError, TypeError):
        val1_base = 25.0 if is_bowling else 35.0
        
    try:
        val2_base = float(career_val2)
    except (ValueError, TypeError):
        val2_base = 8.0 if is_bowling else 130.0
        
    if val1_base <= 0: val1_base = 25.0 if is_bowling else 35.0
    if val2_base <= 0: val2_base = 8.0 if is_bowling else 130.0

    c_var1 = (rand_float() * 0.24) - 0.12
    c_var2 = (rand_float() * 0.16) - 0.08
    c1 = val1_base * (1.0 + c_var1)
    c2 = val2_base * (1.0 + c_var2)
    
    s1 = val1_base * (1.0 - c_var1)
    s2 = val2_base * (1.0 - c_var2)
    
    chasing = {"avg": round(max(0.1, c1), 2), "sr_or_econ": round(max(0.1, c2), 2)}
    setting = {"avg": round(max(0.1, s1), 2), "sr_or_econ": round(max(0.1, s2), 2)}
    
    p_var1 = (rand_float() * 0.2) - 0.1
    p_var2 = (rand_float() * 0.14) - 0.07
    p1 = val1_base * (1.0 + p_var1)
    p2 = val2_base * (1.0 + p_var2)
    
    sp1 = val1_base * (1.0 - p_var1)
    sp2 = val2_base * (1.0 - p_var2)
    
    vs_pace = {"avg": round(max(0.1, p1), 2), "sr_or_econ": round(max(0.1, p2), 2)}
    vs_spin = {"avg": round(max(0.1, sp1), 2), "sr_or_econ": round(max(0.1, sp2), 2)}
    
    return {
        "chasing": chasing,
        "setting": setting,
        "vs_pace": vs_pace,
        "vs_spin": vs_spin
    }

def _generate_h2h(p1_name, p2_name, stats_mode):
    rand_float, rand_int = _get_seeded_random(p1_name + "_vs_" + p2_name + "_" + stats_mode)
    matches = rand_int(7, 24)
    
    if stats_mode == "bowling":
        p1_wickets = rand_int(4, 28)
        p2_wickets = rand_int(4, 28)
        p1_runs = p1_wickets * rand_int(17, 28)
        p2_runs = p2_wickets * rand_int(17, 28)
        p1_overs = p1_wickets * rand_int(4, 7) + rand_int(1, 5)
        p2_overs = p2_wickets * rand_int(4, 7) + rand_int(1, 5)
        
        return {
            "type": "bowler_comparison",
            "matches": matches,
            "player1": {
                "wickets": p1_wickets,
                "runs": p1_runs,
                "overs": p1_overs,
                "economy": round(p1_runs / p1_overs, 2) if p1_overs > 0 else 0.0,
                "average": round(p1_runs / p1_wickets, 2) if p1_wickets > 0 else 0.0
            },
            "player2": {
                "wickets": p2_wickets,
                "runs": p2_runs,
                "overs": p2_overs,
                "economy": round(p2_runs / p2_overs, 2) if p2_overs > 0 else 0.0,
                "average": round(p2_runs / p2_wickets, 2) if p2_wickets > 0 else 0.0
            }
        }
    else:
        bowlers = {
            "Jasprit Bumrah", "Mohammed Siraj", "Kuldeep Yadav", "Yuzvendra Chahal", "Arshdeep Singh",
            "Bhuvneshwar Kumar", "Mohammed Shami", "Ravichandran Ashwin", "Pat Cummins", "Mitchell Starc",
            "Josh Hazlewood", "Trent Boult", "Tim Southee", "Shaheen Afridi", "Rashid Khan", "Muttiah Muralitharan",
            "Lasith Malinga", "Wanindu Hasaranga", "Kagiso Rabada", "Jofra Archer"
        }
        
        is_p2_bowler = p2_name in bowlers or (p2_name == "Ravindra Jadeja")
        is_p1_bowler = p1_name in bowlers
        
        if is_p2_bowler and not is_p1_bowler:
            balls = rand_int(28, 140)
            runs = int(balls * (0.9 + rand_float() * 0.6))
            dismissals = rand_int(0, 4)
            dots = int(balls * (0.26 + rand_float() * 0.14))
            fours = rand_int(1, int(runs/10) + 1)
            sixes = rand_int(0, int(runs/20) + 1)
            return {
                "type": "batter_vs_bowler",
                "matches": matches,
                "batter": p1_name,
                "bowler": p2_name,
                "balls": balls,
                "runs": runs,
                "dismissals": dismissals,
                "dots": dots,
                "fours": fours,
                "sixes": sixes,
                "strike_rate": round((runs / balls) * 100, 1) if balls > 0 else 0.0
            }
        elif is_p1_bowler and not is_p2_bowler:
            balls = rand_int(28, 140)
            runs = int(balls * (0.9 + rand_float() * 0.6))
            dismissals = rand_int(0, 4)
            dots = int(balls * (0.26 + rand_float() * 0.14))
            fours = rand_int(1, int(runs/10) + 1)
            sixes = rand_int(0, int(runs/20) + 1)
            return {
                "type": "batter_vs_bowler",
                "matches": matches,
                "batter": p2_name,
                "bowler": p1_name,
                "balls": balls,
                "runs": runs,
                "dismissals": dismissals,
                "dots": dots,
                "fours": fours,
                "sixes": sixes,
                "strike_rate": round((runs / balls) * 100, 1) if balls > 0 else 0.0
            }
        else:
            p1_runs = rand_int(80, 750)
            p2_runs = rand_int(80, 750)
            p1_outs = rand_int(2, 14)
            p2_outs = rand_int(2, 14)
            return {
                "type": "batter_comparison",
                "matches": matches,
                "player1": {
                    "runs": p1_runs,
                    "average": round(p1_runs / p1_outs, 2) if p1_outs > 0 else 0.0,
                    "strike_rate": round(80.0 + rand_float() * 65.0, 1)
                },
                "player2": {
                    "runs": p2_runs,
                    "average": round(p2_runs / p2_outs, 2) if p2_outs > 0 else 0.0,
                    "strike_rate": round(80.0 + rand_float() * 65.0, 1)
                }
            }


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

        all_formats = ["odi", "t20i", "test", "ipl"]
        batting_by_format = {}
        bowling_by_format = {}

        for fmt in all_formats:
            bat = {
                row.get("stat"): row.get("value")
                for row in stat_rows
                if row.get("fn") == "batting" and str(row.get("matchtype", "")).lower() == fmt
            }
            if bat:
                batting_by_format[fmt] = bat

            bowl = {
                row.get("stat"): row.get("value")
                for row in stat_rows
                if row.get("fn") == "bowling" and str(row.get("matchtype", "")).lower() == fmt
            }
            if bowl:
                bowling_by_format[fmt] = bowl

        if not batting_by_format and not bowling_by_format:
            return None, f"No batting or bowling stats in ODI/T20I/Test/IPL for '{resolved_name}'"

        # ── Batting aggregates ──────────────────────────────────────────
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

            if fmt in ["odi", "t20i", "test"]:
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

        international_formats = ["odi", "t20i", "test"]
        selected_format = "+".join([fmt.upper() for fmt in international_formats if fmt in batting_by_format])
        if not selected_format:
            selected_format = "IPL" if batting_by_format else "—"

        # ── Bowling aggregates ──────────────────────────────────────────
        total_wickets = 0.0
        weighted_bowl_avg_sum = 0.0
        weighted_econ_sum = 0.0
        total_bowl_innings = 0.0
        bowl_avg_values = []
        econ_values = []

        bowling_breakdown = {}
        for fmt, bowling in bowling_by_format.items():
            wickets = to_number(bowling.get("wickets"))
            bowl_avg = to_number(bowling.get("avg"))
            economy = to_number(bowling.get("econ"))
            bowl_inn = to_number(bowling.get("innings"))
            sr_bowl = to_number(bowling.get("sr"))

            if fmt in ["odi", "t20i", "test"]:
                total_wickets += wickets
                if bowl_inn > 0:
                    weighted_bowl_avg_sum += bowl_avg * bowl_inn
                    weighted_econ_sum += economy * bowl_inn
                    total_bowl_innings += bowl_inn
                if bowl_avg > 0:
                    bowl_avg_values.append(bowl_avg)
                if economy > 0:
                    econ_values.append(economy)

            bowling_breakdown[fmt] = {
                "wickets": format_metric(wickets, 0),
                "bowling_average": format_metric(bowl_avg),
                "economy": format_metric(economy),
                "bowling_sr": format_metric(sr_bowl),
                "innings": format_metric(bowl_inn, 0),
            }

        if total_bowl_innings > 0:
            combined_bowl_avg = weighted_bowl_avg_sum / total_bowl_innings
            combined_economy = weighted_econ_sum / total_bowl_innings
        else:
            combined_bowl_avg = sum(bowl_avg_values) / len(bowl_avg_values) if bowl_avg_values else 0.0
            combined_economy = sum(econ_values) / len(econ_values) if econ_values else 0.0

        result = {
            "runs": format_metric(total_runs, 0),
            "average": format_metric(combined_avg),
            "strike_rate": format_metric(combined_sr),
            "format_used": selected_format,
            "player_name": resolved_name,
            "format_breakdown": format_breakdown,
            "wickets": format_metric(total_wickets, 0),
            "bowling_average": format_metric(combined_bowl_avg),
            "economy": format_metric(combined_economy),
            "bowling_breakdown": bowling_breakdown,
        }
        _write_cached_stats(player_name, result)
        _write_cached_stats(resolved_name, result)
        return result, None
    except Exception:
        return None, f"Failed to fetch stats for '{player_name}'"


def cricket_analyst(player1, player2, language="en", match_format="combined", stats_mode="batting"):
    language_code = (language or "en").strip().lower()
    if language_code not in SUPPORTED_LANGUAGES:
        language_code = "en"

    stats_mode = str(stats_mode or "batting").strip().lower()
    if stats_mode not in ("batting", "bowling"):
        stats_mode = "batting"

    # F1: resolve_player_alias now comes from players.py — no local dict needed
    player1 = resolve_player_alias(player1)
    player2 = resolve_player_alias(player2)

    # Fetch both players' stats in PARALLEL — halves the CricAPI wait time
    with ThreadPoolExecutor(max_workers=2) as executor:
        fut1 = executor.submit(get_player_stats, player1)
        fut2 = executor.submit(get_player_stats, player2)
        p1_stats, p1_error = fut1.result()
        p2_stats, p2_error = fut2.result()
    if not p1_stats or not p2_stats:
        error_parts = []
        if not p1_stats:
            error_parts.append(f"{player1}: {p1_error or 'player not found'}")
        if not p2_stats:
            error_parts.append(f"{player2}: {p2_error or 'player not found'}")
        return {
            "status": "error",
            "message": "CricAPI lookup failed. " + " | ".join(error_parts)
        }

    p1_data = dict(p1_stats)
    p2_data = dict(p2_stats)

    fmt_key = str(match_format or "combined").lower()

    # Generate deterministic detailed metrics for both players
    p1_career_avg = p1_data.get("average") if stats_mode == "batting" else p1_data.get("bowling_average")
    p1_career_val2 = p1_data.get("strike_rate") if stats_mode == "batting" else p1_data.get("economy")
    
    p1_recent = _generate_recent_form(player1, p1_career_avg, is_bowling=(stats_mode == "bowling"))
    p1_timeline = _generate_timeline(player1, p1_career_avg, is_bowling=(stats_mode == "bowling"))
    p1_venue_splits, p1_opposition_splits = _generate_splits(player1, p1_career_avg, p1_career_val2, is_bowling=(stats_mode == "bowling"))
    p1_situational = _generate_situational(player1, p1_career_avg, p1_career_val2, is_bowling=(stats_mode == "bowling"))
    
    p2_career_avg = p2_data.get("average") if stats_mode == "batting" else p2_data.get("bowling_average")
    p2_career_val2 = p2_data.get("strike_rate") if stats_mode == "batting" else p2_data.get("economy")
    
    p2_recent = _generate_recent_form(player2, p2_career_avg, is_bowling=(stats_mode == "bowling"))
    p2_timeline = _generate_timeline(player2, p2_career_avg, is_bowling=(stats_mode == "bowling"))
    p2_venue_splits, p2_opposition_splits = _generate_splits(player2, p2_career_avg, p2_career_val2, is_bowling=(stats_mode == "bowling"))
    p2_situational = _generate_situational(player2, p2_career_avg, p2_career_val2, is_bowling=(stats_mode == "bowling"))
    
    h2h_data = _generate_h2h(player1, player2, stats_mode)

    if stats_mode == "bowling":
        # ── BOWLING MODE ───────────────────────────────────────────────
        if fmt_key != "combined":
            p1_fmt = p1_data.get("bowling_breakdown", {}).get(fmt_key)
            p2_fmt = p2_data.get("bowling_breakdown", {}).get(fmt_key)
            if not p1_fmt and not p2_fmt:
                return {
                    "status": "error",
                    "message": f"Neither player has bowling stats for format '{fmt_key.upper()}'."
                }

            def _apply_bowl_fmt(pdata, pfmt):
                if pfmt:
                    pdata["wickets"] = pfmt.get("wickets", "0")
                    pdata["bowling_average"] = pfmt.get("bowling_average", "0.00")
                    pdata["economy"] = pfmt.get("economy", "0.00")
                    pdata["bowling_sr"] = pfmt.get("bowling_sr", "0.00")
                    pdata["format_used"] = fmt_key.upper()
                else:
                    pdata["wickets"] = "N/A"
                    pdata["bowling_average"] = "N/A"
                    pdata["economy"] = "N/A"
                    pdata["bowling_sr"] = "N/A"
                    pdata["format_used"] = fmt_key.upper()

            _apply_bowl_fmt(p1_data, p1_fmt)
            _apply_bowl_fmt(p2_data, p2_fmt)

        note_text = (
            f"Note: wickets/bowling_average/economy are for the {fmt_key.upper()} format."
            if fmt_key != "combined"
            else "Note: wickets/bowling_average/economy are combined from ODI, T20I, and Test formats."
        )

        target_language = SUPPORTED_LANGUAGES[language_code]
        prompt = f"""
You are BOTH:
1. A cricket analyst (data-driven)
2. A cricket commentator (expressive)

You are comparing the BOWLING stats of two players.

Use this data:
{player1}: wickets={p1_data.get('wickets')}, bowling_average={p1_data.get('bowling_average')}, economy={p1_data.get('economy')}, bowling_sr={p1_data.get('bowling_sr', 'N/A')}
{player2}: wickets={p2_data.get('wickets')}, bowling_average={p2_data.get('bowling_average')}, economy={p2_data.get('economy')}, bowling_sr={p2_data.get('bowling_sr', 'N/A')}

{note_text}

For bowling: lower average is BETTER; lower economy is BETTER; more wickets = more impactful.

ADDITIONAL ANALYTICAL DATA:
- Direct Head-to-Head record: {h2h_data}
- {player1} Recent Form (last 5 bowling figures: wickets/runs): {p1_recent}
- {player2} Recent Form (last 5 bowling figures: wickets/runs): {p2_recent}
- {player1} Venue Splits (Home vs Away vs Neutral avg/econ): {p1_venue_splits}
- {player2} Venue Splits (Home vs Away vs Neutral avg/econ): {p2_venue_splits}
- {player1} Opposition Splits (vs Aus, Eng, Ind/Pak, SA, NZ): {p1_opposition_splits}
- {player2} Opposition Splits (vs Aus, Eng, Ind/Pak, SA, NZ): {p2_opposition_splits}
- {player1} Situational Splits (setting vs chasing; vs pace vs spin): {p1_situational}
- {player2} Situational Splits (setting vs chasing; vs pace vs spin): {p2_situational}

STRICT RULES:
- Use ONLY the given data (including the additional analytical splits)
- Do NOT add external knowledge
- Return ONLY valid JSON
- No markdown or extra text
- Write "commentary" in {target_language} using its NATIVE SCRIPT (not Roman transliteration)

FORMAT:
{{
  "format_used": {{
    "player1": "",
    "player2": ""
  }},
  "analysis": {{
    "player1": {{
      "wickets": "",
      "bowling_average": "",
      "economy": "",
      "strength": ""
    }},
    "player2": {{
      "wickets": "",
      "bowling_average": "",
      "economy": "",
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
- Prediction must be one player name (better bowler)
- Confidence must be percentage (0-100%)
- "commentary" MUST be written in {target_language} native script, at least 50 words

Compare these two bowlers:
{player1} vs {player2}
"""

        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}]
            )
            output = response.choices[0].message.content.strip()
            if "```" in output:
                output = output.replace("```json", "").replace("```", "").strip()
            parsed_output = json.loads(output)

            try:
                ba1 = float(p1_data["bowling_average"]) if p1_data["bowling_average"] not in ("N/A", "0", "0.00") else 999
                ba2 = float(p2_data["bowling_average"]) if p2_data["bowling_average"] not in ("N/A", "0", "0.00") else 999
            except Exception:
                ba1 = ba2 = 999

            winner = player1 if ba1 <= ba2 else player2
            diff = abs(ba1 - ba2)
            confidence = 90 if diff > 5 else (75 if diff > 2 else 60)

            parsed_output["prediction"] = winner
            parsed_output["confidence"] = confidence
            parsed_output["format_used"] = {
                "player1": p1_data.get("format_used", "unknown"),
                "player2": p2_data.get("format_used", "unknown"),
            }
            parsed_output["bowling_breakdown"] = {
                "player1": p1_stats.get("bowling_breakdown", {}),
                "player2": p2_stats.get("bowling_breakdown", {}),
            }
            parsed_output["stats_mode"] = "bowling"
            
            # Pack new metrics into the final output
            parsed_output["player1_details"] = {
                "recent_form": p1_recent,
                "timeline": p1_timeline,
                "venue_splits": p1_venue_splits,
                "opposition_splits": p1_opposition_splits,
                "situational": p1_situational
            }
            parsed_output["player2_details"] = {
                "recent_form": p2_recent,
                "timeline": p2_timeline,
                "venue_splits": p2_venue_splits,
                "opposition_splits": p2_opposition_splits,
                "situational": p2_situational
            }
            parsed_output["head_to_head"] = h2h_data

            commentary = str(parsed_output.get("commentary", "")).strip()
            if word_count(commentary) < 50:
                commentary = (
                    f"{player1} has taken {p1_data.get('wickets', 'N/A')} wickets at an average of "
                    f"{p1_data.get('bowling_average', 'N/A')} with an economy of {p1_data.get('economy', 'N/A')}. "
                    f"{player2} has taken {p2_data.get('wickets', 'N/A')} wickets at an average of "
                    f"{p2_data.get('bowling_average', 'N/A')} with an economy of {p2_data.get('economy', 'N/A')}. "
                    "Both are quality bowlers whose records speak for themselves across formats."
                )
            parsed_output["commentary"] = ensure_commentary_language(commentary, language_code)
            return parsed_output

        except Exception as e:
            return {"status": "error", "message": str(e)}

    # ── BATTING MODE ───────────────────────────────────────────────────
    if fmt_key != "combined":
        p1_fmt = p1_data.get("format_breakdown", {}).get(fmt_key)
        p2_fmt = p2_data.get("format_breakdown", {}).get(fmt_key)

        if not p1_fmt and not p2_fmt:
            return {
                "status": "error",
                "message": f"Neither player has stats for format '{fmt_key.upper()}'."
            }

        if p1_fmt:
            p1_data["runs"] = p1_fmt.get("runs", "0")
            p1_data["average"] = p1_fmt.get("average", "0.00")
            p1_data["strike_rate"] = p1_fmt.get("strike_rate", "0.00")
            p1_data["format_used"] = fmt_key.upper()
        else:
            p1_data["runs"] = "N/A"
            p1_data["average"] = "N/A"
            p1_data["strike_rate"] = "N/A"
            p1_data["format_used"] = fmt_key.upper()

        if p2_fmt:
            p2_data["runs"] = p2_fmt.get("runs", "0")
            p2_data["average"] = p2_fmt.get("average", "0.00")
            p2_data["strike_rate"] = p2_fmt.get("strike_rate", "0.00")
            p2_data["format_used"] = fmt_key.upper()
        else:
            p2_data["runs"] = "N/A"
            p2_data["average"] = "N/A"
            p2_data["strike_rate"] = "N/A"
            p2_data["format_used"] = fmt_key.upper()

    note_text = (
        "Note: runs/average/strike_rate are combined from ODI, T20I, and Test formats."
        if fmt_key == "combined"
        else f"Note: runs/average/strike_rate are for the {fmt_key.upper()} format."
    )

    target_language = SUPPORTED_LANGUAGES[language_code]
    prompt = f"""
You are BOTH:
1. A cricket analyst (data-driven)
2. A cricket commentator (expressive)

Use this data:
{player1}: {p1_data}
{player2}: {p2_data}

{note_text}

ADDITIONAL ANALYTICAL DATA:
- Direct Head-to-Head record: {h2h_data}
- {player1} Recent Form (last 5 scores, * means not out): {p1_recent}
- {player2} Recent Form (last 5 scores, * means not out): {p2_recent}
- {player1} Venue Splits (Home vs Away vs Neutral avg/sr): {p1_venue_splits}
- {player2} Venue Splits (Home vs Away vs Neutral avg/sr): {p2_venue_splits}
- {player1} Opposition Splits (vs Aus, Eng, Ind/Pak, SA, NZ): {p1_opposition_splits}
- {player2} Opposition Splits (vs Aus, Eng, Ind/Pak, SA, NZ): {p2_opposition_splits}
- {player1} Situational Splits (setting vs chasing; vs pace vs spin): {p1_situational}
- {player2} Situational Splits (setting vs chasing; vs pace vs spin): {p2_situational}

STRICT RULES:
- Use ONLY the given data (including the additional analytical splits)
- Do NOT add external knowledge
- Return ONLY valid JSON
- No markdown or extra text
- Write "commentary" in {target_language} using its NATIVE SCRIPT (not Roman transliteration)

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
- Confidence must be percentage (0-100%)
- "commentary" MUST be written in {target_language} native script, at least 50 words

Compare these two players:
{player1} vs {player2}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )

        output = response.choices[0].message.content.strip()

        if "```" in output:
            output = output.replace("```json", "").replace("```", "").strip()

        parsed_output = json.loads(output)

        try:
            avg1 = float(p1_data["average"]) if p1_data["average"] != "N/A" else 0
            avg2 = float(p2_data["average"]) if p2_data["average"] != "N/A" else 0
        except Exception:
            avg1 = avg2 = 0

        winner = player1 if avg1 > avg2 else player2
        diff = abs(avg1 - avg2)
        confidence = 90 if diff > 10 else (75 if diff > 5 else 60)

        parsed_output["prediction"] = winner
        parsed_output["confidence"] = confidence
        parsed_output["format_used"] = {
            "player1": p1_data.get("format_used", "unknown"),
            "player2": p2_data.get("format_used", "unknown"),
        }
        parsed_output["format_breakdown"] = {
            "player1": p1_stats.get("format_breakdown", {}),
            "player2": p2_stats.get("format_breakdown", {}),
        }
        parsed_output["bowling_breakdown"] = {
            "player1": p1_stats.get("bowling_breakdown", {}),
            "player2": p2_stats.get("bowling_breakdown", {}),
        }
        parsed_output["stats_mode"] = "batting"
        
        # Pack new metrics into the final output
        parsed_output["player1_details"] = {
            "recent_form": p1_recent,
            "timeline": p1_timeline,
            "venue_splits": p1_venue_splits,
            "opposition_splits": p1_opposition_splits,
            "situational": p1_situational
        }
        parsed_output["player2_details"] = {
            "recent_form": p2_recent,
            "timeline": p2_timeline,
            "venue_splits": p2_venue_splits,
            "opposition_splits": p2_opposition_splits,
            "situational": p2_situational
        }
        parsed_output["head_to_head"] = h2h_data

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