import speech_recognition as sr
import pyttsx3
import requests
import json

# Load player data
with open("players.json") as f:
    player_data = json.load(f)

# Initialize voice
recognizer = sr.Recognizer()
engine = pyttsx3.init()


def speak(text):
    engine.say(text)
    engine.runAndWait()


def listen():
    with sr.Microphone() as source:
        print("🎤 Speak now...")

        recognizer.adjust_for_ambient_noise(source, duration=1)  # 🔥 important

        audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)

    try:
        text = recognizer.recognize_google(audio)
        print("You said:", text)
        return text

    except sr.WaitTimeoutError:
        speak("You did not speak in time")
        return ""

    except sr.UnknownValueError:
        speak("Sorry, I could not understand")
        return ""

    except sr.RequestError:
        speak("Speech service error")
        return ""


# 🔥 Smart player matching
def match_player(name):
    name = name.lower()

    for player in player_data.keys():
        if name in player.lower() or player.lower() in name:
            return player

    return None


# 🔥 Extract players from voice
def extract_players(text):
    text = text.lower()

    # Normalize words
    text = text.replace("versus", "vs")
    text = text.replace("and", "vs")
    text = text.replace("or", "vs")

    parts = text.split("vs")

    if len(parts) == 2:
        raw_p1 = parts[0].strip()
        raw_p2 = parts[1].strip()

        p1 = match_player(raw_p1)
        p2 = match_player(raw_p2)

        return p1, p2

    return None, None


# 🎤 MAIN FLOW
query = listen()

player1, player2 = extract_players(query)

# ❌ If players not found
if player1 is None or player2 is None:
    speak("Sorry, I could not find one or both players")

else:
    # 🔗 Call backend
    response = requests.post(
        "http://127.0.0.1:8000/analyze",
        json={
            "player1": player1,
            "player2": player2
        }
    )

    data = response.json()

    # ❌ Handle backend error
    if data.get("status") == "error":
        print(data["message"])
        speak(data["message"])

    else:
        winner = data["prediction"]
        confidence = data["confidence"]

        result = f"{winner} is likely to win with {confidence} percent confidence"

        print(result)
        speak(result)