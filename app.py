from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os
import requests
import json
import uuid

# -----------------------
# Load environment
# -----------------------

load_dotenv()

FEATHERLESS_API_KEY = os.getenv("FEATHERLESS_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Default ElevenLabs voice
ELEVENLABS_VOICE_ID = os.getenv(
    "ELEVENLABS_VOICE_ID",
    "JBFqnCBsd6RMkjVDRZzb"
)

# -----------------------
# FastAPI setup
# -----------------------

app = FastAPI(title="PlanetSOS Guardian API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure folders exist
os.makedirs("uploads", exist_ok=True)
os.makedirs("audio", exist_ok=True)
os.makedirs("uploads_audio", exist_ok=True)

app.mount("/audio", StaticFiles(directory="audio"), name="audio")
app.mount("/uploads_audio", StaticFiles(directory="uploads_audio"), name="uploads_audio")

# -----------------------
# Helper functions
# -----------------------

def save_upload_file(upload_file: UploadFile, folder: str):
    ext = os.path.splitext(upload_file.filename)[1]
    filename = f"{uuid.uuid4()}{ext}"
    path = os.path.join(folder, filename)

    with open(path, "wb") as f:
        f.write(upload_file.file.read())

    return path


def public_path(folder, path):
    return f"/{folder}/{os.path.basename(path)}"


# -----------------------
# Fake detection (MVP)
# -----------------------

def get_labels_fake(filename):

    name = filename.lower()

    if "fire" in name or "smoke" in name:
        return ["Smoke", "Fire"]

    if "river" in name or "water" in name:
        return ["Plastic", "Bottle", "Water", "Garbage"]

    if "park" in name or "litter" in name or "trash" in name:
        return ["Trash", "Garbage", "Debris"]

    return ["Garbage"]


def map_labels_to_category(labels):

    labels = [x.lower() for x in labels]

    if "fire" in labels or "smoke" in labels:
        return "smoke / fire"

    if "plastic" in labels and "water" in labels:
        return "plastic waste near water"

    if "garbage" in labels or "trash" in labels:
        return "trash dumping"

    return "environmental hazard"


def detect_issue(filename):

    labels = get_labels_fake(filename)
    return map_labels_to_category(labels)


# -----------------------
# Featherless AI analysis
# -----------------------

def analyze_issue_with_featherless(issue, context=""):

    if not FEATHERLESS_API_KEY:
        return {
            "severity": "medium",
            "summary": "Environmental hazard detected.",
            "action": "Further inspection recommended."
        }

    prompt = f"""
You are an environmental risk analysis assistant.

Detected issue: {issue}

Additional reporter context:
{context}

Return JSON:

{{
"severity":"low | medium | high",
"summary":"2 sentence explanation",
"action":"1 short action recommendation"
}}
"""

    url = "https://api.featherless.ai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {FEATHERLESS_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "meta-llama/Meta-Llama-3.1-8B-Instruct",
        "messages": [
            {"role": "system", "content": "Return strict JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }

    try:

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        data = response.json()

        text = data["choices"][0]["message"]["content"]

        return json.loads(text)

    except Exception as e:

        print("Featherless error:", e)

        return {
            "severity": "medium",
            "summary": "Environmental risk detected.",
            "action": "Review the situation."
        }


# -----------------------
# ElevenLabs TTS
# -----------------------

def generate_voice(text, prefix="earth"):

    if not ELEVENLABS_API_KEY:
        return ""

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"

    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2"
    }

    try:

        response = requests.post(url, headers=headers, json=payload, timeout=60)

        response.raise_for_status()

        filename = f"{prefix}_{uuid.uuid4()}.mp3"

        path = os.path.join("audio", filename)

        with open(path, "wb") as f:
            f.write(response.content)

        return public_path("audio", path)

    except Exception as e:

        print("ElevenLabs error:", e)

        return ""


# -----------------------
# ElevenLabs STT
# -----------------------

def transcribe_audio(path):

    if not ELEVENLABS_API_KEY:
        return ""

    url = "https://api.elevenlabs.io/v1/speech-to-text"

    headers = {"xi-api-key": ELEVENLABS_API_KEY}

    try:

        with open(path, "rb") as f:

            files = {"file": f}

            data = {"model_id": "scribe_v2"}

            response = requests.post(
                url,
                headers=headers,
                files=files,
                data=data,
                timeout=60
            )

        response.raise_for_status()

        result = response.json()

        return result.get("text", "")

    except Exception as e:

        print("Transcription error:", e)

        return ""


# -----------------------
# Routes
# -----------------------

@app.get("/")
def home():
    return {"message": "PlanetSOS Guardian backend running"}


@app.get("/health")
def health():
    return {"status": "ok"}


# -----------------------
# Analyze image
# -----------------------

@app.post("/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    reporter_text: str = Form(default=""),
    reporter_transcript: str = Form(default="")
):

    # save image
    path = save_upload_file(file, "uploads")

    image_url = public_path("uploads", path)

    pollution_type = detect_issue(file.filename)

    context = f"{reporter_text} {reporter_transcript}"

    analysis = analyze_issue_with_featherless(pollution_type, context)

    earth_text = f"I detected {pollution_type}. {analysis['summary']} {analysis['action']}"

    audio_url = generate_voice(earth_text, "earth")

    return {
        "image_url": image_url,
        "pollution_type": pollution_type,
        "severity": analysis["severity"],
        "summary": analysis["summary"],
        "action": analysis["action"],
        "earth_voice_text": earth_text,
        "audio_url": audio_url
    }


# -----------------------
# Transcribe voice note
# -----------------------

@app.post("/transcribe")
async def transcribe_voice(
    file: UploadFile = File(...),
    role: str = Form(default="reporter")
):

    path = save_upload_file(file, "uploads_audio")

    audio_url = public_path("uploads_audio", path)

    transcript = transcribe_audio(path)

    return {
        "role": role,
        "audio_url": audio_url,
        "transcript": transcript
    }


# -----------------------
# Convert text to speech
# -----------------------

@app.post("/tts")
async def text_to_speech(
    text: str = Form(...),
    speaker: str = Form(default="responder")
):

    audio_url = generate_voice(text, speaker)

    return {
        "speaker": speaker,
        "text": text,
        "audio_url": audio_url
    }