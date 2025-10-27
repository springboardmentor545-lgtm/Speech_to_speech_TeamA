import os
import azure.cognitiveservices.speech as speechsdk
from config import speech_key, service_region

speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)

auto_detect_source_language_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
    languages=["en-US", "hi-IN"]
)
folder = "speech_samples"

for file in os.listdir(folder):
    if file.endswith(".wav"):
        print(f"Transcribing: {file}")
        audio_input = speechsdk.AudioConfig(filename=os.path.join(folder, file))
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config, 
            audio_config=audio_input, 
            auto_detect_source_language_config=auto_detect_source_language_config
        )

        result = recognizer.recognize_once_async().get()

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            transcript_text = result.text
            detected_language = result.properties.get(
                speechsdk.PropertyId.SpeechServiceConnection_AutoDetectSourceLanguageResult
            )
        else:
            transcript_text = "Error or no speech recognized"
            detected_language = "Unknown"

        print(f"→ [{detected_language}] {transcript_text}\n")
