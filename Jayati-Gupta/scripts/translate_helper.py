import os
import uuid
import requests
from dotenv import load_dotenv

load_dotenv()

TRANSLATOR_KEY = os.getenv("TRANSLATOR_KEY") or os.getenv("AZURE_TRANSLATOR_KEY")
TRANSLATOR_REGION = os.getenv("TRANSLATOR_REGION") or os.getenv("AZURE_TRANSLATOR_REGION")

endpoint = "https://api.cognitive.microsofttranslator.com/translate?api-version=3.0"

def translate_text(text, target_lang):
    """
    Translate text to the target language using Azure Translator API
    """
    if not TRANSLATOR_KEY or not TRANSLATOR_REGION:
        raise ValueError("Translator API key or region missing in .env")
    
    params = f"&to={target_lang}"
    url = endpoint + params

    headers = {
        "Ocp-Apim-Subscription-Key": TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": TRANSLATOR_REGION,
        "Content-Type": "application/json",
        "X-ClientTraceId": str(uuid.uuid4()),
    }

    body = [{"text": text}]

    response = requests.post(url, headers=headers, json=body)
    response.raise_for_status()

    return response.json()[0]["translations"][0]["text"]
