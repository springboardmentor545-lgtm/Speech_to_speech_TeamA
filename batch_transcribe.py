import os
import azure.cognitiveservices.speech as speechsdk
import csv
from config import speech_key, service_region

speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
folder = "speech_samples"
output_file = "transcripts.csv"
rows = []

for file in os.listdir(folder):
    if file.endswith(".wav"):
        print(f"Transcribing: {file}")
        audio_input = speechsdk.AudioConfig(filename=os.path.join(folder, file))
        recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)
        
        full_transcript = []
        done_flag = {"done": False}  # mutable flag

        # Collect recognized speech
        def recognized_cb(evt):
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                full_transcript.append(evt.result.text)

        # Stop flag callback
        def stop_cb(evt):
            done_flag["done"] = True

        recognizer.recognized.connect(recognized_cb)
        recognizer.session_stopped.connect(stop_cb)
        recognizer.canceled.connect(stop_cb)

        # Start continuous recognition
        recognizer.start_continuous_recognition()
        while not done_flag["done"]:
            pass  # wait until session_stopped event triggers
        recognizer.stop_continuous_recognition()

        transcript_text = " ".join(full_transcript) if full_transcript else "Error or no speech recognized"
        rows.append([file, "English", transcript_text])
        print("→", transcript_text)

# Save results in CSV
with open(output_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Filename", "Language", "Transcript"])
    writer.writerows(rows)

print("\nAll files transcribed! Results saved in transcripts.csv ")
import pandas as pd

# Read the CSV you just saved
df = pd.read_csv(output_file)

# Clean filler words
df['Transcript'] = df['Transcript'].str.replace("um", "").str.replace("ah", "")

# Save cleaned CSV
df.to_csv("transcripts_clean.csv", index=False)
print("Cleaned transcripts saved as transcripts_clean.csv ")

