import os
import uuid
import requests
import json
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv


# LOAD ENV

load_dotenv()

SPEECH_KEY = os.getenv("SPEECH_KEY")
SPEECH_REGION = os.getenv("SERVICE_REGION")

TRANSLATOR_KEY = os.getenv("TRANSLATOR_KEY")
TRANSLATOR_REGION = os.getenv("TRANSLATOR_REGION")
TRANSLATOR_ENDPOINT = os.getenv("TRANSLATOR_ENDPOINT", "https://api.cognitive.microsofttranslator.com")

TARGET_LANGS = ["hi", "fr" , "te" , "fr"]   # change languages here



# TRANSLATOR FUNCTION

def translate_text(text, target_langs):
    path = "/translate?api-version=3.0"
    params = "&".join([f"to={lang}" for lang in target_langs])

    url = TRANSLATOR_ENDPOINT.rstrip("/") + path + "&" + params

    headers = {
        "Ocp-Apim-Subscription-Key": TRANSLATOR_KEY,
        "Content-type": "application/json",
        "X-ClientTraceId": str(uuid.uuid4()),
        "Ocp-Apim-Subscription-Region": TRANSLATOR_REGION
    }

    body = [{"Text": text}]

    try:
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        data = response.json()

        translations = data[0]["translations"]
        result = [t["text"] for t in translations]
        return result

    except Exception as e:
        print("Translation error:", e)
        return [""] * len(target_langs)



# SPEECH-TO-TEXT LIVE STREAMING

def start_live_translation():

    # Configure microphone STT
    speech_config = speechsdk.SpeechConfig(
        subscription=SPEECH_KEY,
        region=SPEECH_REGION
    )
    audio_config = speechsdk.AudioConfig(use_default_microphone=True)

    speech_recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config
    )

    print("\n--- Live Translation Started ---")
    print("Speak into your microphone...\n")

    #  When speech is recognized (final result)
    def recognized_handler(evt):
        text = evt.result.text
        if text:
            print("\nYou said:", text)
            translated = translate_text(text, TARGET_LANGS)

            for lang, t in zip(TARGET_LANGS, translated):
                print(f"{lang.upper()}:", t)

    #  When partial result detected
    def recognizing_handler(evt):
        partial = evt.result.text
        if partial:
            print(f"\rListening... {partial}", end="")

    # Connect handlers
    speech_recognizer.recognized.connect(recognized_handler)
    speech_recognizer.recognizing.connect(recognizing_handler)

    # Start continuous recognition
    speech_recognizer.start_continuous_recognition()

    # Keep alive
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\nStopping...")
        speech_recognizer.stop_continuous_recognition()



# MAIN RUN

if __name__ == "__main__":
    start_live_translation()
