import azure.cognitiveservices.speech as speechsdk
import os
from dotenv import load_dotenv

load_dotenv()

speech_key = os.getenv("speech_key")
service_region = os.getenv("service_region")

# if not speech_key:
#     raise ValueError("speech_key not set in environment variables")

# # Test print (only for debugging)
# print("Environment loaded successfully")
# print("speech_key (first 4 chars):", speech_key[:4] + "****")

speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)

print("Say something...")
result = recognizer.recognize_once_async().get()

if result.reason == speechsdk.ResultReason.RecognizedSpeech:
    print("Recognized:", result.text)
else:
    print("No match or cancelled:", result.reason)