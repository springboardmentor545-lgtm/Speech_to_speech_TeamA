import os
import csv
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

# Load .env if available (local only)
load_dotenv()

# ---------- UPDATE THESE PATHS IF NEEDED ----------
INPUT_DIR = "C:/Users/linga/OneDrive/Desktop/speech_project/speechsamples"
OUTPUT_CSV = "C:/Users/linga/OneDrive/Desktop/speech_project/transcripts/transcripts.csv"
# --------------------------------------------------

SPEECH_KEY = os.getenv("speech_key")
SERVICE_REGION = os.getenv("speech_region")

speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SERVICE_REGION)

def transcribe_file(file_path):
    audio_input = speechsdk.AudioConfig(filename=file_path)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)
    result = recognizer.recognize_once_async().get()
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text
    else:
        # return reason for debugging
        return None

os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)

with open(OUTPUT_CSV, mode='w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["filename", "language", "transcript"])
    files = sorted(os.listdir(INPUT_DIR))
    for fname in files:
        if not fname.lower().endswith(".wav"):
            continue
        path = os.path.join(INPUT_DIR, fname)
        # language heuristic: en_... or hi_...
        if fname.startswith("en_"):
            lang = "en"
        elif fname.startswith("hi_"):
            lang = "hi"
        else:
            lang = "unknown"
        print("Transcribing:", fname)
        text = transcribe_file(path)
        writer.writerow([fname, lang, text or ""])
        print("->", text or "<no transcript>")
