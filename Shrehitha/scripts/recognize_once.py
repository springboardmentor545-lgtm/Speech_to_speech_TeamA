import azure.cognitiveservices.speech as speechsdk

speech_key = "G9kY3Nzzj6qvT1lVZ2hhdyRAMuX4Q5K1OZRXvoCXsbvPViJyJTOnJQQJ99BJACGhslBXJ3w3AAAYACOGovng"
service_region = "centralindia"

speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)

print("Say something...")
result = recognizer.recognize_once_async().get()

if result.reason == speechsdk.ResultReason.RecognizedSpeech:
    print("Recognized:", result.text)
else:
    print("No match or cancelled:", result.reason)
