import os
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
SPEECH_KEY = os.getenv("speech_key")
SERVICE_REGION = os.getenv("service_region")

def speech_to_text(file_path, language="en-US"):
    """
    Convert given audio file to text using Azure Speech-to-Text.
    
    Parameters:
        file_path (str) : Path to the .wav file
        language (str)  : Language locale (default English "en-US")
    
    Returns:
        text (str) : Transcribed text
    """
    if not SPEECH_KEY or not SERVICE_REGION:
        return "[Azure Speech Key or Region missing in .env]"

    try:
        speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SERVICE_REGION)
        speech_config.speech_recognition_language = language

        audio_config = speechsdk.AudioConfig(filename=file_path)
        recognizer = speechsdk.SpeechRecognizer(speech_config, audio_config)

        result = recognizer.recognize_once_async().get()

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return result.text

        elif result.reason == speechsdk.ResultReason.NoMatch:
            return "[No speech recognized]"

        else:
            return f"[Error: {result.reason}]"

    except Exception as e:
        return f"[Exception: {str(e)}]"