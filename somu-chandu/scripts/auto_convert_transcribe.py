import os
import csv
import subprocess
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

load_dotenv()
SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
SERVICE_REGION = os.getenv("AZURE_REGION")

print("🔄 AUTOMATIC CONVERSION + TRANSCRIPTION")
print("=" * 50)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "speech_samples")
OUTPUT_CSV = os.path.join(BASE_DIR, "transcripts", "transcripts.csv")

def convert_to_wav(input_file, output_dir):
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = os.path.join(output_dir, f"{base_name}.wav")
    
    if os.path.exists(output_file):
        print(f"   ✅ WAV version exists: {base_name}.wav")
        return output_file

    cmd = ['ffmpeg', '-i', input_file, '-acodec', 'pcm_s16le', '-ac', '1', '-ar', '16000', '-y', output_file]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"   ✅ Converted: {base_name}.wav")
        return output_file
    except Exception as e:
        print(f"   ❌ Conversion failed: {e}")
        return None

def transcribe_file(file_path, language="en-US"):
    if not SPEECH_KEY or not SERVICE_REGION:
        return "[Missing Azure credentials]"
    
    print(f"   🔊 Transcribing: {os.path.basename(file_path)}")
    try:
        speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SERVICE_REGION)
        speech_config.speech_recognition_language = language
        audio_config = speechsdk.audio.AudioConfig(filename=file_path)
        recognizer = speechsdk.SpeechRecognizer(speech_config, audio_config)
        result = recognizer.recognize_once_async().get()
        return result.text if result.reason == speechsdk.ResultReason.RecognizedSpeech else "[Recognition failed]"
    except Exception as e:
        return f"[Error: {e}]"

def get_language_info(filename):
    if filename.startswith("te_"): return "te-IN", "Telugu"
    elif filename.startswith("hi_"): return "hi-IN", "Hindi"
    else: return "en-US", "English"

def main():
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    
    all_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(('.wav', '.mp3', '.m4a', '.mp4'))]
    if not all_files:
        print("❌ No audio files found!")
        return
    
    wav_files = []
    for f in all_files:
        path = os.path.join(INPUT_DIR, f)
        if not f.endswith(".wav"):
            converted = convert_to_wav(path, INPUT_DIR)
            if converted: wav_files.append(converted)
        else:
            wav_files.append(path)
    
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["filename", "language", "language_name", "transcript"])
        for wf in wav_files:
            lang_code, lang_name = get_language_info(os.path.basename(wf))
            transcript = transcribe_file(wf, lang_code)
            writer.writerow([os.path.basename(wf), lang_code, lang_name, transcript])
    
    print(f"\n🎉 All transcripts saved to: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
