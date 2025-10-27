# file: scripts/transcribe_files.py

import os

import csv

import azure.cognitiveservices.speech as speechsdk



SPEECH_KEY = "G9kY3Nzzj6qvT1lVZ2hhdyRAMuX4Q5K1OZRXvoCXsbvPViJyJTOnJQQJ99BJACGhslBXJ3w3AAAYACOGovng"

SERVICE_REGION = "centralindia"

INPUT_DIR = r"C:\Users\HP\Downloads\Rizia_Prabin\samples"   # set your folder

OUTPUT_CSV = r"C:\Users\HP\Downloads\Rizia_Prabin\transcripts\transcripts.csv"  # set your output csv file



speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SERVICE_REGION)

audio_config = None



def transcribe_file(file_path):

    audio_input = speechsdk.AudioConfig(filename=file_path)

    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)

    result = recognizer.recognize_once_async().get()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:

        return result.text

    else:

        return None



os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)



with open(OUTPUT_CSV, mode='w', newline='', encoding='utf-8') as csvfile:

    writer = csv.writer(csvfile)

    writer.writerow(["filename", "language", "transcript"])

    for fname in sorted(os.listdir(INPUT_DIR)):

        if not fname.lower().endswith(".wav"):

            continue

        lang = "en" if fname.startswith("en_") else ("hi" if fname.startswith("hi_") else "unknown")

        path = os.path.join(INPUT_DIR, fname)

        print("Transcribing", fname)

        text = transcribe_file(path)

        writer.writerow([fname, lang, text or ""])

        print("->", text)

