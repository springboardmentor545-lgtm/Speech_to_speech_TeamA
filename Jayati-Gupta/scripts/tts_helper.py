import azure.cognitiveservices.speech as speechsdk
import os
from dotenv import load_dotenv

load_dotenv()

SPEECH_KEY = os.getenv("SPEECH_KEY") or os.getenv("AZURE_SPEECH_KEY")
SERVICE_REGION = os.getenv("SERVICE_REGION") or os.getenv("AZURE_REGION")

def synthesize_speech(text, voice, out_path):
    """
    Convert text to speech using Azure TTS and save to a .wav file
    """
    if not SPEECH_KEY or not SERVICE_REGION:
        raise ValueError("Azure Speech Key or Region missing in .env")

    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SERVICE_REGION)
    speech_config.speech_synthesis_voice_name = voice

    audio_config = speechsdk.audio.AudioOutputConfig(filename=out_path)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    result = synthesizer.speak_text_async(text).get()

    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        raise Exception(f"Speech synthesis failed: {result.reason}")

    return out_path
