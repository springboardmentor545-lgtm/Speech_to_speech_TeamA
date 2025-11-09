import os, csv
import azure.cognitiveservices.speech as speechsdk

SPEECH_KEY = "G9kY3Nzzj6qvT1lVZ2hhdyRAMuX4Q5K1OZRXvoCXsbvPViJyJTOnJQQJ99BJACGhslBXJ3w3AAAYACOGovng"
SERVICE_REGION = "centralindia"
INPUT_DIR = "speech_samples"
OUTPUT_CSV = "transcripts/transcripts.csv"

os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)


def transcribe_file(file_path, language):
    speech_config = speechsdk.SpeechConfig(
        subscription=SPEECH_KEY, region=SERVICE_REGION
    )
    speech_config.speech_recognition_language = language
    audio_input = speechsdk.AudioConfig(filename=file_path)
    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config, audio_config=audio_input
    )
    result = recognizer.recognize_once_async().get()
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text
    else:
        return ""


with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["filename", "language", "transcript"])

    for fname in sorted(os.listdir(INPUT_DIR)):
        if not fname.lower().endswith(".wav"):
            continue

        
        if fname.startswith("en_") or fname.startswith("eng_"):
            lang_code = "en-IN"
            lang_short = "en"
        elif fname.startswith("hi_") or fname.startswith("hindi_"):
            lang_code = "hi-IN"
            lang_short = "hi"
        else:
            lang_code = "en-IN"
            lang_short = "unknown"

        path = os.path.join(INPUT_DIR, fname)
        print(f"Transcribing {fname} ({lang_code}) ...")

        text = transcribe_file(path, lang_code)
        writer.writerow([fname, lang_short, text])
        print("→", fname + ":", text)
