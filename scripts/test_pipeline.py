"""
Test script for the Speech-to-Speech pipeline
Tests individual components and the full pipeline
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

load_dotenv()

def test_credentials():
    """Test if all required credentials are present."""
    print("🔐 Testing Azure Credentials...")
    print("=" * 50)
    
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    speech_region = os.getenv("AZURE_REGION")
    translator_key = os.getenv("AZURE_TRANSLATOR_KEY")
    translator_region = os.getenv("AZURE_TRANSLATOR_REGION") or os.getenv("AZURE_REGION")
    
    checks = {
        "Azure Speech Key": bool(speech_key),
        "Azure Speech Region": bool(speech_region),
        "Azure Translator Key": bool(translator_key),
        "Azure Translator Region": bool(translator_region)
    }
    
    all_passed = True
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check}")
        if not passed:
            all_passed = False
    
    print()
    return all_passed


def test_translator():
    """Test the translation module."""
    print("🌐 Testing Translation Module...")
    print("=" * 50)
    
    try:
        from translator import translate_text
        
        test_text = "Hello, this is a test."
        result = translate_text(test_text, target_languages=["hi", "es"])
        
        if result["success"]:
            print(f"✅ Translation successful!")
            print(f"   Original: {result['original_text']}")
            print(f"   Source: {result['source_language']}")
            for lang, trans in result["translations"].items():
                print(f"   {lang}: {trans}")
            return True
        else:
            print(f"❌ Translation failed: {result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ Error testing translator: {e}")
        return False


def test_stt():
    """Test Speech-to-Text (basic check)."""
    print("\n🎤 Testing Speech-to-Text...")
    print("=" * 50)
    
    try:
        import azure.cognitiveservices.speech as speechsdk
        
        speech_key = os.getenv("AZURE_SPEECH_KEY")
        speech_region = os.getenv("AZURE_REGION")
        
        if not speech_key or not speech_region:
            print("❌ Missing Speech credentials")
            return False
        
        speech_config = speechsdk.SpeechConfig(
            subscription=speech_key,
            region=speech_region
        )
        
        print("✅ Speech SDK initialized successfully")
        print("   (Full STT test requires microphone access)")
        return True
    except Exception as e:
        print(f"❌ Error testing STT: {e}")
        return False


def test_tts():
    """Test Text-to-Speech (basic check)."""
    print("\n🔊 Testing Text-to-Speech...")
    print("=" * 50)
    
    try:
        import azure.cognitiveservices.speech as speechsdk
        
        speech_key = os.getenv("AZURE_SPEECH_KEY")
        speech_region = os.getenv("AZURE_REGION")
        
        if not speech_key or not speech_region:
            print("❌ Missing Speech credentials")
            return False
        
        tts_config = speechsdk.SpeechConfig(
            subscription=speech_key,
            region=speech_region
        )
        tts_config.speech_synthesis_voice_name = "en-US-JennyNeural"
        
        print("✅ TTS SDK initialized successfully")
        print("   (Full TTS test requires audio output)")
        return True
    except Exception as e:
        print(f"❌ Error testing TTS: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 PIPELINE COMPONENT TESTS")
    print("=" * 50)
    print()
    
    results = []
    
    # Test credentials
    results.append(("Credentials", test_credentials()))
    
    if not all(r[1] for r in results):
        print("\n⚠️  Some credentials are missing. Please check your .env file.")
        print("   Continuing with available tests...\n")
    
    # Test translator
    results.append(("Translator", test_translator()))
    
    # Test STT
    results.append(("Speech-to-Text", test_stt()))
    
    # Test TTS
    results.append(("Text-to-Speech", test_tts()))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
    
    all_passed = all(r[1] for r in results)
    
    print()
    if all_passed:
        print("🎉 All tests passed! Pipeline is ready to use.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

