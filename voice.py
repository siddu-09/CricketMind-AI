import speech_recognition as sr
import pyttsx3
import requests
from stt import transcribe_wav_bytes, extract_players_from_transcript

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
        try:
            audio = recognizer.listen(source, timeout=8, phrase_time_limit=8)
        except sr.WaitTimeoutError:
            speak("You did not speak in time")
            return ""

    wav_bytes = audio.get_wav_data(convert_rate=16000, convert_width=2)
    text, error = transcribe_wav_bytes(wav_bytes, language="en")

    if error:
        print(error)
        speak(error)
        return ""

    print("You said:", text)
    return text


# 🔥 Extract players from voice
def extract_players(text):
    return extract_players_from_transcript(text)


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