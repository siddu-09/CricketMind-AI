import os
import json
from dotenv import load_dotenv
from groq import Groq

# load env variables
load_dotenv()

# initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# load player data
with open("players.json") as f:
    player_data = json.load(f)


def cricket_analyst(question):
    prompt = f"""
You are an expert cricket analyst like a TV commentator.

Use this data:
{player_data}

Instructions:
- Analyze using stats
- Compare players clearly
- Use bullet points
- Give final conclusion
- Avoid generic answers

Question: {question}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content