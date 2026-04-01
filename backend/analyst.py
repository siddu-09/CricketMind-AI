import os
import json
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Load player data
with open("players.json") as f:
    player_data = json.load(f)


def cricket_analyst(player1, player2):
    if player1 not in player_data or player2 not in player_data:
        return {
            "status": "error",
            "message": "One or both players not found in dataset"
        }
    prompt = f"""
You are BOTH:
1. A cricket analyst (data-driven)
2. A cricket commentator (expressive)

Use this data:
{player_data}

STRICT RULES:
- Use ONLY the given data
- Do NOT add external knowledge
- Return ONLY valid JSON
- No markdown or extra text

FORMAT:

{{
  "analysis": {{
    "virat_kohli": {{
      "runs": "",
      "average": "",
      "strike_rate": "",
      "strength": ""
    }},
    "rohit_sharma": {{
      "runs": "",
      "average": "",
      "strike_rate": "",
      "strength": ""
    }}
  }},
  "comparison": [
    "",
    "",
    ""
  ],
  "commentary": "",
  "verdict": "",
  "prediction": "",
  "confidence": ""
}}
IMPORTANT:
- Prediction must be one player name
- Confidence must be percentage (0–100%)

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

        # 🔥 Clean markdown if AI adds it
        if "```" in output:
            output = output.replace("```json", "").replace("```", "").strip()

        # 🔥 Convert to JSON
        parsed_output = json.loads(output)

        return parsed_output

    except Exception as e:
        # 🔥 Always return safe response (no crash)
        return {
            "status": "error",
            "message": str(e)
        }