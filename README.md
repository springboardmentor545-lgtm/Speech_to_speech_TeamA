# Speech_to_speech_TeamA
# AI-Powered Real-Time Speech Translation

**Project Goal:** This project aims to develop a real-time, speech-to-speech translation system. It will convert live spoken content (from English/Hindi) into 12+ languages, making content on OTT platforms more accessible to a multilingual audience.

**Document Purpose:** This README tracks the technical progress of the project, detailing the setup steps, API usage, and I/O for each completed milestone.

---

## Milestone 1: Speech Recognition & Data Collection

This milestone involved setting up the Azure Speech-to-Text service to transcribe a batch of pre-recorded audio files. Several additional features were also developed to enhance the project.

### Setup Steps

1.  **Local Environment:** Installed Python 3.9+, pip, and `ffmpeg` (for audio conversion).
2.  **Folder Structure:** Created the main project folders: `/speech_samples`, `/scripts`, and `/transcripts`.
3.  **Azure SDK:** Installed the Azure Speech SDK for Python using the command:
    `pip install azure-cognitiveservices-speech`

### API Details

* **Service:** Azure Cognitive Services - **Speech Service**
* **Authentication:** Used a **Speech Key** and **Service Region** (e.g., `centralindia`) from the Azure portal.
* **SDK:** `azure.cognitiveservices.speech` (Python)
* **Key Functions:**
    * `speechsdk.AudioConfig(filename=...)` was used for *file-based* transcription.
    * `speechsdk.AudioConfig(use_default_microphone=True)` was used for *live* transcription.
* **Language Specificity:** The `language="hi-IN"` parameter was set in the recognizer to correctly transcribe Hindi.

### Batch Transcription from Files

This feature uses the `transcribe_files.py` script to process all audio files from the `/speech_samples` folder.

* **Input:** 10 standardized audio files (`.wav` format) placed in the `/speech_samples` folder.
    * `en_1audio.wav`
    * `hi_1audio.wav`
* **Output:** A single `transcripts.csv` file created in the `/transcripts` folder.
    ```csv
    filename,language,transcript
    en_1audio.wav,en,Historic moment for Indian cricket Virat Kohli...
    hi_1audio.wav,hi,आज मौसम साफ बना हुआ है और तापमान सामान्य रहेगा...
    ```

### Additional Features

In addition to the core task, two extra features were implemented to improve the project's functionality:

1.  **Live Microphone Transcription:** A second script (`recognize_once.py`) was developed to capture and transcribe speech directly from the user's microphone in real-time. The script detects speech, stops on silence or a voice command, and saves the result.

    * **Sample Input:** Live speech spoken into the default microphone after running the script.
    * **Sample Output (Live Terminal Session):**
        ```bash
        PS C:\...> python scripts\recognize_once.py
        VOICE RECORDER WITH AUTO-STOP
        Say 'end recording' to stop, or press Ctrl+C manually.

        Recording started... Speak now!
        Hello.
        End recording.

        Stop command detected!
        Recording stopped

        FINAL TRANSCRIPTION SAVED!
        Saved to: ...\transcripts\recognized_output.csv

        TRANSCRIPT:
        Hello.
        ```

2.  **Automated Audio Conversion (in-code):** The main `transcribe_files.py` script was enhanced to automatically detect and convert any non-WAV audio file (like MP3, M4A, etc.) using `ffmpeg`. This creates a more robust pipeline where any audio format can be processed without manual conversion.

### Milestone 1 Snippets
<img width="871" height="130" alt="1" src="https://github.com/user-attachments/assets/b5171e63-081c-4c0b-9ad2-2a69080f46e8" />
<br>
transcripts.csv file output
<br>
<br>

<img width="845" height="278" alt="snipp" src="https://github.com/user-attachments/assets/0c170356-06b0-4e2a-aa5f-f6c8c1f994cc" />
<br>
Terminal window output showing our additional feature



---

## Milestone 2: Translation Module & STT Integration

This milestone involved creating a "Translation Module" and integrating it with the **file-based STT output** (`transcripts.csv`) from Milestone 1.

### Setup Steps

1.  **Azure Resource:** Created a new **Azure Translator** resource in the Azure portal.
2.  **Configuration:** Set the pricing tier to **F0 (Free)** and the region to `centralindia` to match the Speech service.
3.  **Library:** Installed the `requests` library to communicate with the Translator's REST API:
    `pip install requests`
4.  **Integration:** Wrote a new script (`translate_text.py`) to automatically read the `transcripts.csv` from Milestone 1 and pass its contents to the new translation module.

### API Details

* **Service:** Azure AI - **Translator** (REST API)
* **Endpoint:** `https://api.cognitive.microsofttranslator.com/`
* **API Version:** 3.0
* **Authentication:** Used HTTP headers for the **Translator Key** (`Ocp-Apim-Subscription-Key`) and **Region** (`Ocp-Apim-Subscription-Region`).
* **Method:** Sent `POST` requests to the `/translate` endpoint with a JSON body containing the text to be translated.

### Sample Input / Output

* **Input:** The `transcripts.csv` file generated by Milestone 1. The script reads each row of this file.
    ```csv
    filename,language,transcript
    en_1audio.wav,en,Historic moment for Indian cricket Virat Kohli...
    hi_1audio.wav,hi,आज मौसम साफ बना हुआ है...
    ```

* **Output:** A live print to the terminal for each row processed from the CSV file.
    ```bash
    ==================================================
    Original Text (en): Historic moment for Indian cricket Virat Kohli...

    Translated Outputs:
       HI: भारतीय क्रिकेट विराट कोहली के लिए ऐतिहासिक पल...
       FR: Moment historique for le cricket indien Virat Kohli...
       ES: Momento histórico para el cricket indio Virat Kohli...
       DE: Historischer Moment für das indische Cricket Virat Kohli...
    ==================================================
    
    ==================================================
    Original Text (hi): आज मौसम साफ बना हुआ है...

    Translated Outputs:
       EN: Today the weather is clear...
       FR: Aujourd'hui, le temps est clair...
       ES: Hoy el tiempo está despejado...
       DE: Heute ist das Wetter klar...
    ==================================================
    ```
### Workflow Summary 

🎙 Audio Input  
     ↓  
🗣 Speech-to-Text (Azure Speech Service)  
     ↓  
📝 transcripts.csv  
     ↓  
🌍 Text Translation (Azure Translator API)  
     ↓  
🧠 Streamlit Frontend for Display  
     ↓  
🔊 (Next) Neural TTS for Voice Output

### Milestone 2 Snippets
<img width="771" height="176" alt="image" src="https://github.com/user-attachments/assets/b3146c01-0bd5-4133-832b-3afb58814d04" />
<br>
Terminal window output showing the conversion of one of the audio files into 4 different languages
<br>
<br>
<img width="703" height="392" alt="image" src="https://github.com/user-attachments/assets/cec6d3e7-b846-42bb-86a0-1561185854d4" />
<br>
Frontend UI Demonstration
A web-based user interface was developed to provide a visual front-end for the translation service. It allows a user to "Speak" or "Upload" an audio file, see the recognized text, and get the final translation.

---

## Milestone 3: Real-Time Speech-to-Speech Integration

This milestone focused on moving from file-based processing to a fully **real-time, event-driven pipeline**. The system now captures live audio, translates it, and synthesizes speech instantly, meeting the "End-to-End Latency < 2 seconds" requirement.

### Setup Steps

1.  **Folder Structure:** Created a dedicated `milestone3` folder with subdirectories for `temp` storage and `logs`.
2.  **Orchestrator Script:** Developed `orchestrator.py`, a main control script that manages the asynchronous events between the Microphone, Azure STT, Azure Translator, and Azure TTS.
3.  **Silence Optimization:** Tuned the Azure `Speech_SegmentationSilenceTimeoutMs` to **2000ms** to prevent the system from cutting off sentences too early during live speaking.

### API Details

* **Service:** Azure Cognitive Services - **Speech Service (Text-to-Speech)**
* **Function:** `speech_synthesizer.speak_text_async()`
* **Streaming:** Enabled streaming synthesis to ensure playback starts (`t5`) as soon as the first byte of audio arrives (`t4`), rather than waiting for the whole file to generate.
* **Voice Selection:** Configured to use specific neural voices (e.g., `hi-IN-SwaraNeural`) for natural-sounding output.

### Latency Instrumentation & Architecture

To meet the performance goals, the pipeline instruments specific timestamps for every utterance:

* **$t_0$ (Audio Start):** Mic detects speech.
* **$t_2$ (STT Final):** Text transcription received.
* **$t_3$ (Translation):** Translated text received.
* **$t_4$ (TTS First Byte):** First audio byte received from Azure (measured via `synthesizing` event).
* **$t_5$ (Playback):** Audio begins playing on the client.

**Formula:** `End-to-End Latency = t5 - t0`

### Sample Input / Output (Live Demo)

* **Input:** Live speech into the microphone (e.g., "What a beautiful shot by Virat Kohli").
* **Output (Audio):** The computer immediately speaks the translation in Hindi.
* **Output (Terminal Report):** A real-time latency report is generated for every phrase to verify performance.

```text
Listening: What a beautiful shot by Virat Kohli...

[STT Final] What a beautiful shot by Virat Kohli.
[Translated] विराट कोहली का कितना खूबसूरत शॉट है।

----------------------------------------
⚡ LATENCY REPORT for Utterance a1b2
   Speech-to-Text: 0.842s
   Translation:    0.125s
   Text-to-Speech: 0.310s  <-- (Real First Byte)
   TOTAL (E2E):    1.277s  <-- (Target: <2.0s)
----------------------------------------
```
### Milestone 3 Snippets

