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

STRICT RULES:
- Return ONLY valid JSON
- Do NOT include markdown (no ```json)
- Do NOT include explanation
- Do NOT include extra text

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