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


def cricket_analyst(question):
    prompt = f"""
You are an elite cricket analyst.

Use this data:
{player_data}

IMPORTANT:
- Return ONLY valid JSON
- Do NOT add explanation outside JSON
- Do NOT use \\n
- Keep values simple and clear

FORMAT:

{{
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
  }},
  "comparison": [
    "",
    "",
    ""
  ],
  "verdict": ""
}}

Question: {question}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    output = response.choices[0].message.content

    # Convert string → JSON safely
    try:
        return json.loads(output)
    except:
        return {
            "error": "Invalid JSON from AI",
            "raw_output": output
        }