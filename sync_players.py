#!/usr/bin/env python3
import os
import re
import json
import argparse
import requests
from dotenv import load_dotenv

# Load env variables from .env if present
load_dotenv()

def normalize_key(text):
    cleaned = re.sub(r"[^a-z0-9\s]", " ", str(text or "").lower())
    return re.sub(r"\s+", " ", cleaned).strip()

def sync_players(offset=0, pages=1):
    apikey = os.getenv("CRICAPI_KEY")
    if not apikey:
        print("❌ Error: CRICAPI_KEY not found in environment or .env file.")
        return

    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, "players.json")

    # Load existing aliases
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                aliases = json.load(f)
        except Exception as e:
            print(f"⚠️ Warning: Could not read players.json ({e}). Starting fresh.")
            aliases = {}
    else:
        aliases = {}

    initial_count = len(aliases)
    added_players = set()
    new_aliases_count = 0

    url = "https://api.cricapi.com/v1/players"

    for page in range(pages):
        current_offset = offset + (page * 25)
        print(f"🔄 Fetching players page {page+1}/{pages} (offset: {current_offset})...")
        try:
            resp = requests.get(url, params={"apikey": apikey, "offset": current_offset}, timeout=15)
            if resp.status_code != 200:
                print(f"❌ API returned status code {resp.status_code}")
                break

            data = resp.json()
            if data.get("status") == "failure":
                reason = data.get("reason", "Unknown failure reason")
                print(f"❌ API Failure: {reason}")
                break

            players_list = data.get("data", [])
            if not players_list:
                print("ℹ️ No more players returned from CricAPI.")
                break

            for p in players_list:
                name = p.get("name")
                if not name:
                    continue

                # Prepare candidate aliases
                canonical_name = name.strip()
                normalized_full = normalize_key(canonical_name)

                # 1. Full name alias
                if normalized_full and (normalized_full not in aliases or aliases[normalized_full] == canonical_name):
                    if normalized_full not in aliases:
                        aliases[normalized_full] = canonical_name
                        new_aliases_count += 1
                        added_players.add(canonical_name)

                # 2. Part-name aliases (first and last name)
                tokens = normalized_full.split()
                if len(tokens) > 1:
                    for token in [tokens[0], tokens[-1]]:
                        if len(token) > 3:  # Only add part-names longer than 3 characters
                            # To prevent conflicts, only add if the token doesn't exist
                            if token not in aliases:
                                aliases[token] = canonical_name
                                new_aliases_count += 1
                                added_players.add(canonical_name)

        except Exception as e:
            print(f"❌ Error fetching from CricAPI: {e}")
            break

    # Save back to players.json if any updates
    if new_aliases_count > 0:
        # Sort aliases alphabetically by key
        sorted_aliases = dict(sorted(aliases.items()))
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(sorted_aliases, f, indent=2)
            print(f"✅ Successfully synced and updated players.json!")
            print(f"   - Original aliases: {initial_count}")
            print(f"   - New aliases added: {new_aliases_count}")
            print(f"   - Total aliases now: {len(sorted_aliases)}")
            print(f"   - Players updated: {', '.join(sorted(added_players))}")
        except Exception as e:
            print(f"❌ Error writing players.json: {e}")
    else:
        print("ℹ️ No new players or aliases were added.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync new players from CricAPI and append to players.json")
    parser.add_argument("--offset", type=int, default=0, help="Starting offset for CricAPI (default: 0)")
    parser.add_argument("--pages", type=int, default=1, help="Number of pages (25 players per page) to fetch (default: 1)")
    args = parser.parse_args()

    sync_players(offset=args.offset, pages=args.pages)
