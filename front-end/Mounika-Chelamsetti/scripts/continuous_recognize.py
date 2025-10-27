import azure.cognitiveservices.speech as speechsdk
import os
from dotenv import load_dotenv
from pathlib import Path
import time

# ✅ Load .env from parent folder
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)

speech_key = os.getenv("G9kY3Nzzj6qvT1lVZ2hhdyRAMuX4Q5K1OZRXvoCXsbvPViJyJTOnJQQJ99BJACGhslBXJ3w3AAAYACOGovng")
service_region = os.getenv("centralindia")

speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
audio_config = speechsdk.AudioConfig(use_default_microphone=True)
recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

def stop_cb(evt):
    print("🛑 Stopping recognition on event:", evt)
    recognizer.stop_continuous_recognition()

def recognized_cb(evt):
    print("🗣️ Recognized:", evt.result.text)

recognizer.recognized.connect(recognized_cb)
recognizer.canceled.connect(lambda evt: print("⚠️ Canceled:", evt))
recognizer.session_stopped.connect(stop_cb)

recognizer.start_continuous_recognition()
print("🎧 Listening... Press Ctrl+C to stop.")

try:
    while True:
        time.sleep(0.5)
except KeyboardInterrupt:
    recognizer.stop_continuous_recognition()
