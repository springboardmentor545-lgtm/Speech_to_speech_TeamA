import os
import csv
import subprocess
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🔄 AUTOMATIC CONVERSION + TRANSCRIPTION")
print("=" * 50)

# Configuration from environment variables
BASE_DIR = os.getenv('BASE_DIR', r"C:\Users\csomu\Desktop\Speech_to_speech_TeamA\somu-chandu")
INPUT_DIR = os.path.join(BASE_DIR, os.getenv('INPUT_DIR', 'speech_samples'))
OUTPUT_CSV = os.path.join(BASE_DIR, os.getenv('OUTPUT_DIR', 'transcripts'), "transcripts.csv")

# Azure credentials from environment variables
SPEECH_KEY = os.getenv('SPEECH_KEY')
SERVICE_REGION = os.getenv('SERVICE_REGION', 'centralindia')

if not SPEECH_KEY:
    raise ValueError("❌ SPEECH_KEY not found in environment variables")

# ... rest of your existing functions remain the same ...
def convert_to_wav(input_file, output_dir):
    """
    Convert any audio file to Azure-compatible WAV format
    """
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = os.path.join(output_dir, f"{base_name}.wav")
    
    # Skip if WAV already exists
    if os.path.exists(output_file):
        print(f"   ✅ WAV version already exists: {base_name}.wav")
        return output_file
    
    # FFmpeg conversion command
    cmd = [
        'ffmpeg', '-i', input_file,      # Input file
        '-acodec', 'pcm_s16le',          # PCM 16-bit
        '-ac', '1',                      # Mono
        '-ar', '16000',                  # 16 kHz
        '-y',                            # Overwrite
        output_file
    ]
    
    try:
        print(f"   🔄 Converting: {os.path.basename(input_file)} → {base_name}.wav")
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"   ✅ Conversion successful!")
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Conversion failed: {e}")
        return None
    except FileNotFoundError:
        print("   ❌ FFmpeg not installed! Using original file.")
        return input_file

def transcribe_file(file_path, language="en-US"):
    """
    Transcribe a WAV file using Azure Speech-to-Text
    """
    try:
        print(f"   🔊 Transcribing: {os.path.basename(file_path)}")
        
        speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SERVICE_REGION)
        speech_config.speech_recognition_language = language
        
        audio_config = speechsdk.audio.AudioConfig(filename=file_path)
        recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
        
        result = recognizer.recognize_once_async().get()
        
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            print("   ✅ Transcription successful!")
            return result.text
        else:
            print("   ❌ Recognition failed")
            return "[Recognition failed]"
            
    except Exception as e:
        print(f"   💥 Error: {str(e)}")
        return f"[Error: {str(e)}]"

def get_language_info(filename):
    """
    Determine language based on filename prefix
    Returns: (language_code, language_name)
    """
    if filename.startswith('te_'):
        return "te-IN", "Telugu"
    elif filename.startswith('hi_'):
        return "hi-IN", "Hindi"
    else:
        return "en-US", "English"

def main():
    """
    Main function: Convert all audio files → Transcribe all WAV files
    """
    # Create directories
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    
    # Check input directory
    if not os.path.exists(INPUT_DIR):
        print(f"❌ Directory doesn't exist: {INPUT_DIR}")
        return
    
    # Get all audio files
    all_audio_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(('.wav', '.mp3', '.m4a', '.mp4', '.aac', '.flac'))]
    
    if not all_audio_files:
        print("❌ No audio files found in speech_samples!")
        print(f"Please add your audio files to: {INPUT_DIR}")
        return
    
    print(f"📁 Found {len(all_audio_files)} audio file(s):")
    
    # Step 1: Convert all non-WAV files to WAV
    wav_files = []
    for filename in all_audio_files:
        file_path = os.path.join(INPUT_DIR, filename)
        
        if filename.lower().endswith('.wav'):
            language_code, language_name = get_language_info(filename)
            print(f"   ✅ WAV ({language_name}): {filename}")
            wav_files.append(file_path)
        else:
            # Convert non-WAV files
            language_code, language_name = get_language_info(filename)
            print(f"   🎵 Non-WAV ({language_name}): {filename}")
            converted_file = convert_to_wav(file_path, INPUT_DIR)
            if converted_file and converted_file.endswith('.wav'):
                wav_files.append(converted_file)
    
    print(f"\n🎯 Ready to transcribe {len(wav_files)} WAV file(s)")
    print("Supported languages:")
    print("   🇺🇸 English (default)")
    print("   🇮🇳 Hindi - use 'hi_' prefix")
    print("   🇮🇳 Telugu - use 'te_' prefix")
    
    # Step 2: Transcribe all WAV files
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["filename", "language", "language_name", "transcript", "original_format"])
        
        for wav_file in wav_files:
            filename = os.path.basename(wav_file)
            
            # Determine language
            language_code, language_name = get_language_info(filename)
            
            # Find original format
            original_format = "wav"
            for audio_file in all_audio_files:
                if audio_file.startswith(filename.replace('.wav', '')):
                    original_format = audio_file.split('.')[-1]
                    break
            
            # Transcribe
            print(f"\n🌐 Processing {language_name} file: {filename}")
            transcript = transcribe_file(wav_file, language_code)
            
            # Write to CSV
            writer.writerow([filename, language_code, language_name, transcript, original_format])
            
            print(f"\n📝 RESULT for {filename}:")
            print(f"   Original: {original_format.upper()} → WAV")
            print(f"   Language: {language_name}")
            print(f"   Transcript: {transcript}")
            print("-" * 50)
    
    print(f"\n🎉 All done!")
    print(f"💾 Results saved to: {OUTPUT_CSV}")
    print("📝 All transcripts are preserved in their native scripts (English, Hindi, Telugu)")

if __name__ == "__main__":
    main()