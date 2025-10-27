# file: scripts/continuous_recognize.py
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv
import os
import time

# ✅ Load credentials from .env
load_dotenv()
speech_key = os.getenv("AZURE_SPEECH_KEY")
service_region = os.getenv("AZURE_REGION")

# ✅ Validate credentials
if not speech_key or not service_region:
    print("❌ Azure credentials missing. Please check your .env file.")
    exit(1)

# ✅ Configure speech recognizer
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

# ✅ Event handlers
def recognized_cb(evt):
    if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print(f"🎯 Recognized: {evt.result.text}")
    elif evt.result.reason == speechsdk.ResultReason.NoMatch:
        print("⚠️ No speech could be recognized.")

def canceled_cb(evt):
    print(f"❌ Canceled: {evt.reason}")
    recognizer.stop_continuous_recognition()

def stopped_cb(evt):
    print("🟢 Session stopped.")
    recognizer.stop_continuous_recognition()

# ✅ Connect events
recognizer.recognized.connect(recognized_cb)
recognizer.canceled.connect(canceled_cb)
recognizer.session_stopped.connect(stopped_cb)

# ✅ Start continuous recognition
print("🎤 Listening continuously... (Press Ctrl+C to stop)\n")
recognizer.start_continuous_recognition_async().get()

try:
    while True:
        time.sleep(0.5)
except KeyboardInterrupt:
    print("\n🛑 Stopping recognition...")
    recognizer.stop_continuous_recognition_async().get()
    print("✅ Recognition stopped.")
