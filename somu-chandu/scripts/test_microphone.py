"""
Test script to check microphone access and Azure Speech SDK
"""
import os
import sys
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

load_dotenv()

def test_microphone():
    """Test if microphone is accessible"""
    try:
        print("Testing microphone access...")
        
        # Test basic microphone access
        import pyaudio
        p = pyaudio.PyAudio()
        
        print("Available audio devices:")
        for i in range(p.get_device_count()):
            dev_info = p.get_device_info_by_index(i)
            if dev_info['maxInputChannels'] > 0:
                print(f"  {i}: {dev_info['name']} (Input channels: {dev_info['maxInputChannels']})")
        
        p.terminate()
        print("✓ PyAudio test passed")
        
    except Exception as e:
        print(f"✗ PyAudio test failed: {e}")
        return False
    
    # Test Azure Speech SDK
    try:
        speech_key = os.getenv("AZURE_SPEECH_KEY")
        speech_region = os.getenv("AZURE_REGION")
        
        if not speech_key or not speech_region:
            print("✗ Missing Azure credentials")
            return False
        
        print("Testing Azure Speech SDK...")
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        
        # Create recognizer but don't start recognition
        recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
        print("✓ Azure Speech SDK test passed")
        
        return True
        
    except Exception as e:
        print(f"✗ Azure Speech SDK test failed: {e}")
        return False

if __name__ == "__main__":
    test_microphone()