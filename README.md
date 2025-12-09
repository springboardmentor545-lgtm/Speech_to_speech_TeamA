# 🌐 Voice Without Borders : AI-Powered Real-Time Speech Translation


![Status](https://img.shields.io/badge/Status-Active-success?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=flat-square)
![Azure](https://img.shields.io/badge/Azure-Cognitive%20Services-0078D4?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

> **Bridging language barriers in real-time through event-driven AI orchestration.**

---
## 📑 Table of Contents
- [📖 Overview](#-overview)
- [✨ Key Features](#-key-features)
- [🏗 System Architecture](#-system-architecture)
- [🚀 User Interface](#-user-interface)
- [🛠️ Tech Stack](#️-tech-stack)
- [⚙️ Installation & Setup](#setup)
- [🕹️ Usage Guide](#️-usage-guide)
- [📊 Performance Logs](#-performance-logs)

---

## 📖 Overview

This project implements a high-performance, bidirectional speech-to-speech translation system designed to increase accessibility for multilingual audiences on OTT platforms.

Moving beyond simple transcription, this solution offers a **unified translation engine** capable of processing two distinct audio sources with sub-2-second latency:
1.  **Live Input:** Real-time microphone capture for conversation translation.
2.  **Content Input:** Instant audio extraction and translation of YouTube videos via URL.
3.  **File Input:** Direct upload and processing of pre-recorded audio files (WAV/MP3)



---

## ✨ Key Features

*   **⚡ Low-Latency Orchestration:** Achieves an end-to-end processing time of **<2000ms** using asynchronous Python event loops.
*   **🎥 YouTube Integration:** Integrated `yt-dlp` pipeline to extract, transcode, and translate video audio streams on the fly.
*   **🌍 Multi-Language Support:** Powered by Azure Cognitive Services to support 12+ global languages (English, Hindi, French, German, etc.).
*   **🎨 Modern Bento-Grid Dashboard:** A high-contrast, dark-mode user interface designed for accessibility, featuring real-time status indicators and audio visualization.
*   **🧠 Smart Silence Detection:** Optimized VAD (Voice Activity Detection) to handle natural pauses in speech without cutting context.

---

## 🏗 System Architecture

The system relies on a Python-based orchestrator that manages the flow of data between the Audio I/O layer and Azure Cloud Services.



```mermaid
graph TD
    %% --- Color Palette Definitions ---
    classDef source fill:#d4edda,stroke:#28a745,stroke-width:2px,color:#155724
    classDef logic fill:#fff3cd,stroke:#ffc107,stroke-width:3px,color:#856404
    classDef cloud fill:#cce5ff,stroke:#007bff,stroke-width:2px,color:#004085
    classDef output fill:#f8d7da,stroke:#dc3545,stroke-width:2px,color:#721c24

    %% --- STAGE 1: INPUT SOURCES ---
    subgraph S1 ["🟢 Stage 1: Input Sources"]
        direction TB
        Mic["🎤 Microphone<br/>(Live Voice)"]
        YT["📺 YouTube Video<br/>(URL Extraction)"]
    end

    %% --- STAGE 2: THE BRAIN ---
    subgraph S2 ["🟠 Stage 2: The Controller"]
        Python{"🐍 Python App<br/>(Orchestrator)"}
    end

    %% --- STAGE 3: AZURE AI ---
    subgraph S3 ["🔵 Stage 3: Azure Cloud Processing"]
        direction TB
        STT["👂 Speech-to-Text<br/>(Audio ➔ Text)"]
        Trans["🌍 Translator<br/>(Eng ➔ Target Lang)"]
        TTS["🗣️ Text-to-Speech<br/>(Text ➔ Audio)"]
    end

    %% --- STAGE 4: USER OUTPUT ---
    subgraph S4 ["🔴 Stage 4: Final Output"]
        direction TB
        Speaker["🔊 Speaker<br/>(Play Audio)"]
        Display["📜 Screen<br/>(Show Subtitles)"]
    end

    %% --- FLOW CONNECTIONS ---
    
    %% 1. Input to Python
    Mic -->|Raw Audio Stream| Python
    YT -->|Extracted Audio| Python

    %% 2. Python to Cloud Pipeline
    Python -->|1. Send Audio| STT
    STT -->|2. Return Text| Trans
    Trans -->|3. Return Translated Text| TTS
    TTS -->|4. Return Synth Audio| Python

    %% 3. Python to Output
    Python ===>|Final Audio| Speaker
    Python -.->|Live Transcript| Display

    %% --- APPLY STYLES ---
    class Mic,YT source
    class Python logic
    class STT,Trans,TTS cloud
    class Speaker,Display output
```
### 📉 Latency Modeling

To ensure real-time performance, the pipeline optimizes the following time-to-audio equation:

<div align="center">
  <img src="https://latex.codecogs.com/svg.image?\color{White}\text{Latency}=t_{playback}-t_{start}\approx\sum(t_{transcription}+t_{translation}+t_{synthesis})" alt="Latency Equation" />
</div>


---

## 🚀 User Interface

The application features a modern, Bento-grid style dashboard optimized for clarity.


![page 1_page-0001 (1)](https://github.com/user-attachments/assets/210b8a9a-436f-4b69-86f8-54475950df04)
![page 1_page-0002 (2) (2) (1)](https://github.com/user-attachments/assets/b05b3041-42fe-45be-8570-395b4d292ced)





**Dashboard Elements:**
- Video Speech Translation
- Real-Time & Text Translation
- Batch Processing
- Diagnostics

---

## 🛠️ Tech Stack

| Component       | Technology Used                     |
|----------------|-------------------------------------|
| Core Logic     | Python 3.9+                         |
| Cloud AI       | Azure Speech SDK, Azure Translator  |
| Audio Processing | FFmpeg, PyAudio, yt-dlp          |
| Frontend       | Streamlit (Bento UI)                |
| Data Handling  | Pandas, CSV                         |

---

## <a id="setup"></a>⚙️ Installation & Setup

### 1. Prerequisites
- Python 3.9+
- FFmpeg installed and added to PATH
- Azure Subscription

### 2. Clone and Install

```bash
git clone https://github.com/your-username/Speech_to_speech_project.git
cd Speech_to_speech_project

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```
### 3. Configuration

Create a `.env` file:

```ini
SPEECH_KEY=your_azure_speech_key
SPEECH_REGION=centralindia
TRANSLATOR_KEY=your_azure_translator_key
TRANSLATOR_REGION=centralindia
```
## 🕹️ Usage Guide

### **Mode A: Live Conversation**

- Run the application:

```bash
streamlit run app.py
```
- Select **RealTime STT & Translation** from the sidebar  
- Click **Start Listening**  
- Speak naturally — the system detects silence and auto-translates  

![page 2_page-0001 (1)](https://github.com/user-attachments/assets/2f92284a-a03d-43b0-83e4-b9c64103931e)
![page 2_page-0002 (1)](https://github.com/user-attachments/assets/dad633f7-bfa6-47ff-a0c0-3b1aae5f44f0)

---

### **Mode B: YouTube Translation**

- Select **Video Speech Translation** from the sidebar  
- Paste a valid link (e.g., news clip, speech)
- Click Process Video
- The system extracts audio, transcribes it, and reads out the translated speech  

![page 5_page-0001 (1)](https://github.com/user-attachments/assets/7ba52a5a-c82f-4155-936c-360c7a2e575f)
![page 5_page-0002 (1)](https://github.com/user-attachments/assets/9e4d5d81-fcd8-48ab-94d3-021d049e3688)


---
---

### **Mode C: Batch Processing**

- Select **Batch Processing** from the sidebar
- Upload a supported audio file (WAV)
- The system processes the file and generates the transcript

![page 3_page-0001 (1)](https://github.com/user-attachments/assets/41259340-cf7b-4c19-84b3-abcf74fed69b)

## 📊 Performance Logs

The system maintains logs to measure translation accuracy and response times.

<details>
<summary><b>📂 Click to view sample CSV Output</b></summary>

| Filename | Language | Transcript | Translation |
| :--- | :--- | :--- | :--- |
| `live_rec_01.wav` | en-US | "Historic moment for Indian cricket." | "भारतीय क्रिकेट के लिए ऐतिहासिक पल।" |
| `yt_clip_04.wav` | hi-IN | "आज मौसम साफ बना हुआ है..." | "The weather remains clear today..." |

</details>
© 2025 Vidzai Digital
<br>

<div align="center">

### 🔥 Found this helpful ?

If so, please consider giving it a **⭐ Star** on GitHub!


</div>

<br>
