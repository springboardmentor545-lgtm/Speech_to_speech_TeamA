import os
import csv
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

load_dotenv()
SPEECH_KEY = os.getenv("G9kY3Nzzj6qvT1lVZ2hhdyRAMuX4Q5K1OZRXvoCXsbvPViJyJTOnJQQJ99BJACGhslBXJ3w3AAAYACOGovng")
SERVICE_REGION = os.getenv("centralindia")

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "speech_samples")
OUTPUT_DIR = os.path.join(BASE_DIR, "transcripts")
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "transcripts.csv")

print("🚀 FIXED AZURE SPEECH-TO-TEXT")
print("=" * 50)

def transcribe_file(file_path, language="en-US"):
    if not SPEECH_KEY or not SERVICE_REGION:
        return "[Missing Azure credentials]"
    
    try:
        speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SERVICE_REGION)
        speech_config.speech_recognition_language = language
        audio_config = speechsdk.audio.AudioConfig(filename=file_path)
        recognizer = speechsdk.SpeechRecognizer(speech_config, audio_config)
        result = recognizer.recognize_once_async().get()
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return result.text
        return "[No speech recognized]"
    except Exception as e:
        return f"[Error: {str(e)}]"

def get_language_info(filename):
    if filename.startswith('te_'): return "te-IN", "Telugu"
    elif filename.startswith('hi_'): return "hi-IN", "Hindi"
    else: return "en-US", "English"

def main():
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    wav_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith('.wav')]
    if not wav_files:
        print("❌ No WAV files found in speech_samples/")
        return
    
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "language", "language_name", "transcript"])
        for file in wav_files:
            file_path = os.path.join(INPUT_DIR, file)
            lang_code, lang_name = get_language_info(file)
            transcript = transcribe_file(file_path, lang_code)
            writer.writerow([file, lang_code, lang_name, transcript])
            print(f"✅ {file} → {transcript}")
    
    print(f"\n💾 Saved all transcripts to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()