import os, csv
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

load_dotenv()

speech_key = os.getenv("speech_key")
service_region = os.getenv("service_region")
input_dir = "speech_samples"
output_csv = "transcripts/transcripts.csv"

# for dirpath, dirnames, filenames in os.walk(INPUT_DIR):
#     print("Current Directory:", dirpath)
#     print("Subdirectories:", dirnames)
#     print("Files:", filenames)
#     print("-" * 40)

speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)

def transcribe_file(file_path):
    audio_input = speechsdk.AudioConfig(filename=file_path)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)
    result = recognizer.recognize_once_async().get()
    return result.text if result.reason == speechsdk.ResultReason.RecognizedSpeech else None

os.makedirs(os.path.dirname(output_csv), exist_ok=True)

with open(output_csv, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(["filename", "language", "transcript"])
    for fname in sorted(os.listdir(input_dir)):
        if not fname.endswith(".wav"): continue
        lang = "en" if fname.startswith("en_") else "hi"
        text = transcribe_file(os.path.join(input_dir, fname))
        writer.writerow([fname, lang, text or ""])
        print(f"{fname} -> {text}")
