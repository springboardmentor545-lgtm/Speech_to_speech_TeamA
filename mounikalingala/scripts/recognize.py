import os
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

load_dotenv()  

speech_key = os.getenv("speech_key")
service_region = os.getenv("speech_region")

speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)

print("Say something (listening once)...")
result = recognizer.recognize_once_async().get()

if result.reason == speechsdk.ResultReason.RecognizedSpeech:
    print("Recognized:", result.text)
else:
    print("No match or cancelled:", result.reason)
