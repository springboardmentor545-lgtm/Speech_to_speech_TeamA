import os, csv
import azure.cognitiveservices.speech as speechsdk

SPEECH_KEY = "G9kY3Nzzj6qvT1lVZ2hhdyRAMuX4Q5K1OZRXvoCXsbvPViJyJTOnJQQJ99BJACGhslBXJ3w3AAAYACOGovng"
SERVICE_REGION = "centralindia"
INPUT_DIR = "speech_samples"
OUTPUT_CSV = "transcripts/transcripts.csv"

speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SERVICE_REGION)


def transcribe_file(path):
    audio = speechsdk.AudioConfig(filename=path)
    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config, audio_config=audio
    )
    result = recognizer.recognize_once_async().get()
    return (
        result.text
        if result.reason == speechsdk.ResultReason.RecognizedSpeech
        else None
    )


os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["filename", "language", "transcript"])
    for fname in sorted(os.listdir(INPUT_DIR)):
        if fname.endswith(".wav"):
            lang = (
                "en"
                if fname.startswith("en_")
                else "hi"
                if fname.startswith("hi_")
                else "unknown"
            )
            text = transcribe_file(os.path.join(INPUT_DIR, fname))
            writer.writerow([fname, lang, text or ""])
            print(f"→ {fname}: {text}")
