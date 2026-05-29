"""
players.py — CricketMind-AI centralised player registry (Feature F1)
Single source of truth. Import this in analyst.py, stt.py, and ui.py.
"""

import re
from difflib import SequenceMatcher

# ── Master alias dictionary ────────────────────────────────────────────────────
# Add any new player here ONCE. All three modules will pick it up automatically.

COMMON_PLAYER_ALIASES = {
    # ── Virat Kohli ──
    "virat kohli": "Virat Kohli",
    "kohli": "Virat Kohli",
    "virat": "Virat Kohli",
    "king kohli": "Virat Kohli",
    "vk": "Virat Kohli",
    "king": "Virat Kohli",

    # ── Rohit Sharma ──
    "rohit sharma": "Rohit Sharma",
    "rohit": "Rohit Sharma",
    "hitman": "Rohit Sharma",
    "ro": "Rohit Sharma",

    # ── MS Dhoni ──
    "ms dhoni": "MS Dhoni",
    "dhoni": "MS Dhoni",
    "msd": "MS Dhoni",
    "captain cool": "MS Dhoni",
    "thala": "MS Dhoni",
    "mahi": "MS Dhoni",

    # ── Sachin Tendulkar ──
    "sachin tendulkar": "Sachin Tendulkar",
    "sachin": "Sachin Tendulkar",
    "tendulkar": "Sachin Tendulkar",
    "little master": "Sachin Tendulkar",
    "master blaster": "Sachin Tendulkar",
    "god of cricket": "Sachin Tendulkar",

    # ── Jasprit Bumrah ──
    "jasprit bumrah": "Jasprit Bumrah",
    "bumrah": "Jasprit Bumrah",
    "jasprit": "Jasprit Bumrah",

    # ── Ravindra Jadeja ──
    "ravindra jadeja": "Ravindra Jadeja",
    "jadeja": "Ravindra Jadeja",
    "jaddu": "Ravindra Jadeja",
    "sir jadeja": "Ravindra Jadeja",

    # ── Hardik Pandya ──
    "hardik pandya": "Hardik Pandya",
    "hardik": "Hardik Pandya",
    "pandya": "Hardik Pandya",

    # ── Shubman Gill ──
    "shubman gill": "Shubman Gill",
    "gill": "Shubman Gill",
    "shubman": "Shubman Gill",

    # ── KL Rahul ──
    "kl rahul": "KL Rahul",
    "rahul": "KL Rahul",
    "kl": "KL Rahul",
    "lokesh rahul": "KL Rahul",

    # ── Ravichandran Ashwin ──
    "ravichandran ashwin": "Ravichandran Ashwin",
    "ashwin": "Ravichandran Ashwin",
    "r ashwin": "Ravichandran Ashwin",

    # ── Mohammed Siraj ──
    "mohammed siraj": "Mohammed Siraj",
    "siraj": "Mohammed Siraj",

    # ── Yashasvi Jaiswal ──
    "yashasvi jaiswal": "Yashasvi Jaiswal",
    "jaiswal": "Yashasvi Jaiswal",
    "yashasvi": "Yashasvi Jaiswal",

    # ── Babar Azam ──
    "babar azam": "Babar Azam",
    "babar": "Babar Azam",
    "king babar": "Babar Azam",

    # ── Shaheen Afridi ──
    "shaheen afridi": "Shaheen Afridi",
    "shaheen": "Shaheen Afridi",
    "shaheen shah afridi": "Shaheen Afridi",

    # ── Mohammad Rizwan ──
    "mohammad rizwan": "Mohammad Rizwan",
    "rizwan": "Mohammad Rizwan",

    # ── Pat Cummins ──
    "pat cummins": "Pat Cummins",
    "cummins": "Pat Cummins",
    "pat": "Pat Cummins",

    # ── Steve Smith ──
    "steve smith": "Steve Smith",
    "smith": "Steve Smith",
    "smudge": "Steve Smith",

    # ── David Warner ──
    "david warner": "David Warner",
    "warner": "David Warner",

    # ── Travis Head ──
    "travis head": "Travis Head",
    "head": "Travis Head",
    "travis": "Travis Head",

    # ── Ben Stokes ──
    "ben stokes": "Ben Stokes",
    "stokes": "Ben Stokes",

    # ── Joe Root ──
    "joe root": "Joe Root",
    "root": "Joe Root",

    # ── Jofra Archer ──
    "jofra archer": "Jofra Archer",
    "archer": "Jofra Archer",
    "jofra": "Jofra Archer",

    # ── Kagiso Rabada ──
    "kagiso rabada": "Kagiso Rabada",
    "rabada": "Kagiso Rabada",
    "kg rabada": "Kagiso Rabada",
    "kg": "Kagiso Rabada",

    # ── Kane Williamson ──
    "kane williamson": "Kane Williamson",
    "williamson": "Kane Williamson",
    "kane": "Kane Williamson",

    # ── Trent Boult ──
    "trent boult": "Trent Boult",
    "boult": "Trent Boult",

    # ── Shakib Al Hasan ──
    "shakib al hasan": "Shakib Al Hasan",
    "shakib": "Shakib Al Hasan",

    # ── Wanindu Hasaranga ──
    "wanindu hasaranga": "Wanindu Hasaranga",
    "hasaranga": "Wanindu Hasaranga",
}


def resolve_player_alias(name: str) -> str:
    """
    Resolve a typed name or alias to its canonical form.
    Falls back to the original input (title-cased) if no match found.
    Used by analyst.py and ui.py.

    Examples:
        resolve_player_alias("king kohli")  -> "Virat Kohli"
        resolve_player_alias("hitman")      -> "Rohit Sharma"
        resolve_player_alias("Joe Root")    -> "Joe Root"
    """
    if not name or not name.strip():
        return name
    key = name.strip().lower()
    if key in COMMON_PLAYER_ALIASES:
        return COMMON_PLAYER_ALIASES[key]
    # Partial match: check if any alias is a substring of the input
    for alias in sorted(COMMON_PLAYER_ALIASES, key=len, reverse=True):
        if alias in key:
            return COMMON_PLAYER_ALIASES[alias]
    return name.strip().title()


def _normalize(text: str) -> str:
    cleaned = re.sub(r"[^a-z0-9\s]", " ", str(text or "").lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def _match_player_name(fragment: str) -> str:
    """
    Match a transcript fragment to a canonical player name.
    Used internally by extract_players_from_transcript.
    """
    normalized = _normalize(fragment)
    if not normalized:
        return ""

    if normalized in COMMON_PLAYER_ALIASES:
        return COMMON_PLAYER_ALIASES[normalized]

    for alias in sorted(COMMON_PLAYER_ALIASES, key=len, reverse=True):
        if alias in normalized:
            return COMMON_PLAYER_ALIASES[alias]

    tokens = normalized.split()
    candidates = [normalized]
    candidates.extend(tokens)
    if len(tokens) > 1:
        candidates.extend(" ".join(tokens[i: i + 2]) for i in range(len(tokens) - 1))

    best_alias = ""
    best_score = 0.0
    best_candidate_len = 0
    for candidate in candidates:
        for alias in COMMON_PLAYER_ALIASES:
            score = SequenceMatcher(a=candidate, b=alias).ratio()
            if score > best_score:
                best_score = score
                best_alias = alias
                best_candidate_len = len(candidate)

    threshold = 0.70 if best_candidate_len <= 5 else 0.78
    if best_alias and best_score >= threshold:
        return COMMON_PLAYER_ALIASES[best_alias]

    return ""


def extract_players_from_transcript(text: str) -> tuple:
    """
    Extract up to two canonical player names from a voice transcript.
    Used by stt.py and ui.py.

    Examples:
        extract_players_from_transcript("compare kohli and rohit")
            -> ("Virat Kohli", "Rohit Sharma")
    """
    normalized = _normalize(text)
    if not normalized:
        return None, None

    normalized = re.sub(
        r"\b(vs\.?|v\/?s|versus|verses|against|and|with|or)\b", " vs ", normalized
    )
    normalized = re.sub(r"\s+", " ", normalized).strip()

    parts = [part.strip() for part in normalized.split(" vs ") if part.strip()]

    if len(parts) >= 2:
        player1 = _match_player_name(parts[0])
        player2 = _match_player_name(parts[1])
        if player1 and player2 and player1.lower() != player2.lower():
            return player1, player2

    found = []
    for alias in sorted(COMMON_PLAYER_ALIASES, key=len, reverse=True):
        if alias in normalized:
            canonical = COMMON_PLAYER_ALIASES[alias]
            if canonical not in found:
                found.append(canonical)
            if len(found) == 2:
                return found[0], found[1]

    return None, None