import os
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

load_dotenv()
speech_key = os.getenv("speech_key")
service_region = os.getenv("speech_region")

speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

def stop_cb(evt):
    print('CLOSING on {}'.format(evt))
    recognizer.stop_continuous_recognition()

def recognized_cb(evt):
    print("RECOGNIZED: {}".format(evt.result.text))

recognizer.recognized.connect(recognized_cb)
recognizer.canceled.connect(lambda evt: print("CANCELED: {}".format(evt)))
recognizer.session_stopped.connect(stop_cb)

recognizer.start_continuous_recognition()
print("Listening... press Ctrl+C to stop.")
try:
    import time
    while True:
        time.sleep(0.5)
except KeyboardInterrupt:
    recognizer.stop_continuous_recognition()
