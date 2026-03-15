from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os
import requests
import json
import uuid
from datetime import datetime
from typing import Optional

# Import Supabase service and auth routes
from routes_auth import router as auth_router
from services.supabase_service import supabase_service

# -----------------------
# Load environment
# -----------------------

load_dotenv()

FEATHERLESS_API_KEY = os.getenv("FEATHERLESS_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")

# -----------------------
# App setup
# -----------------------

app = FastAPI(title="PlanetSOS Guardian API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication routes
app.include_router(auth_router)

# -----------------------
# Folders
# -----------------------

os.makedirs("uploads", exist_ok=True)
os.makedirs("audio", exist_ok=True)
os.makedirs("uploads_audio", exist_ok=True)
os.makedirs("data", exist_ok=True)

TICKETS_FILE = "data/tickets.json"

if not os.path.exists(TICKETS_FILE):
    with open(TICKETS_FILE, "w") as f:
        json.dump([], f)

app.mount("/audio", StaticFiles(directory="audio"), name="audio")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/uploads_audio", StaticFiles(directory="uploads_audio"), name="uploads_audio")

# -----------------------
# File + JSON helpers
# -----------------------

def load_tickets():
    with open(TICKETS_FILE, "r") as f:
        return json.load(f)

def save_tickets(tickets):
    with open(TICKETS_FILE, "w") as f:
        json.dump(tickets, f, indent=2)

def save_upload_file(upload_file: UploadFile, folder: str):
    ext = os.path.splitext(upload_file.filename or "")[1]
    if not ext:
        ext = ".bin"
    filename = f"{uuid.uuid4()}{ext}"
    path = os.path.join(folder, filename)

    with open(path, "wb") as f:
        f.write(upload_file.file.read())

    return path

def public_path(folder, path):
    return f"/{folder}/{os.path.basename(path)}"

def now_iso():
    return datetime.utcnow().isoformat() + "Z"

# -----------------------
# Fake issue detection for MVP
# -----------------------

def get_labels_fake(filename):
    name = filename.lower()

    if "fire" in name or "smoke" in name:
        return ["Smoke", "Fire"]

    if "river" in name or "water" in name:
        return ["Plastic", "Bottle", "Water", "Garbage"]

    if "park" in name or "litter" in name or "trash" in name:
        return ["Trash", "Garbage", "Debris"]

    if "chemical" in name or "spill" in name:
        return ["Chemical", "Hazard", "Spill"]

    if "pothole" in name or "road" in name:
        return ["Road", "Damage", "Pothole"]

    return ["Garbage"]

def map_labels_to_issue_type(labels):
    labels = [x.lower() for x in labels]

    if "fire" in labels or "smoke" in labels:
        return "fire hazard"

    if "chemical" in labels or "spill" in labels or "hazard" in labels:
        return "chemical spill"

    if "plastic" in labels and "water" in labels:
        return "plastic waste near water"

    if "road" in labels or "pothole" in labels:
        return "pothole"

    if "garbage" in labels or "trash" in labels or "debris" in labels:
        return "trash dumping"

    return "environmental hazard"

def detect_issue(filename):
    labels = get_labels_fake(filename)
    return map_labels_to_issue_type(labels)

# -----------------------
# Category + routing logic
# -----------------------

def classify_category(issue_type):
    if issue_type in ["trash dumping"]:
        return "household issue"

    if issue_type in ["pothole"]:
        return "public issue"

    if issue_type in ["chemical spill", "fire hazard"]:
        return "private issue"

    if issue_type in ["plastic waste near water", "environmental hazard"]:
        return "environmental issue"

    return "public issue"

def assign_responder(issue_type, risk_level):
    if risk_level == "critical":
        return "emergency"

    if issue_type in ["chemical spill", "fire hazard"]:
        return "police_fire_medical"

    if issue_type in ["pothole"]:
        return "municipal"

    if issue_type in ["plastic waste near water", "trash dumping", "environmental hazard"]:
        return "environmental"

    return "general"

# -----------------------
# Featherless AI
# -----------------------

def fallback_ai_analysis(issue_type, category, location_text=""):
    if issue_type == "chemical spill":
        return {
            "risk_level": "critical",
            "health_concern": "Possible toxic exposure for nearby people.",
            "ecosystem_impact": "Can contaminate land and water and harm wildlife.",
            "summary": "A possible chemical spill has been detected. This may pose immediate danger to public health and the surrounding environment.",
            "action": "Escalate immediately and keep people away from the area."
        }

    if issue_type == "fire hazard":
        return {
            "risk_level": "high",
            "health_concern": "Smoke and flames can harm nearby people and air quality.",
            "ecosystem_impact": "Can damage habitats and spread quickly.",
            "summary": "A fire-related hazard has been detected. This may threaten both nearby residents and local ecosystems.",
            "action": "Alert emergency responders and contain the area."
        }

    if issue_type == "pothole":
        return {
            "risk_level": "low",
            "health_concern": "Low direct health concern but can cause traffic accidents.",
            "ecosystem_impact": "Minimal ecosystem impact.",
            "summary": "A pothole has been detected in a public area. This mainly poses a local infrastructure and road safety issue.",
            "action": "Assign to municipal maintenance for repair."
        }

    if issue_type == "plastic waste near water":
        return {
            "risk_level": "high",
            "health_concern": "Can indirectly affect human health through water contamination.",
            "ecosystem_impact": "Can harm aquatic life and spread pollution through waterways.",
            "summary": "Plastic waste has been detected near water. This may harm aquatic ecosystems and spread pollution further downstream.",
            "action": "Assign environmental cleanup and monitor the site."
        }

    if issue_type == "trash dumping":
        return {
            "risk_level": "medium",
            "health_concern": "Can attract pests and create sanitation issues.",
            "ecosystem_impact": "Can degrade nearby habitats and soil quality.",
            "summary": "Trash dumping has been detected. This may create sanitation issues and damage the surrounding area over time.",
            "action": "Schedule cleanup and inspect for repeated dumping."
        }

    return {
        "risk_level": "medium",
        "health_concern": "Potential health concern depending on proximity and exposure.",
        "ecosystem_impact": "May negatively affect the nearby environment.",
        "summary": "An issue has been detected and should be reviewed.",
        "action": "Inspect the location and assign the appropriate responder."
    }

def analyze_issue_with_featherless(issue_type, category, latitude="", longitude="", reporter_text="", reporter_transcript=""):
    if not FEATHERLESS_API_KEY:
        return fallback_ai_analysis(issue_type, category)

    prompt = f"""
You are an AI incident triage assistant for a civic and environmental response platform.

Incident details:
- issue_type: {issue_type}
- category: {category}
- latitude: {latitude}
- longitude: {longitude}
- reporter_text: {reporter_text}
- reporter_transcript: {reporter_transcript}

Return ONLY valid JSON in this exact format:
{{
  "risk_level": "low | medium | high | critical",
  "health_concern": "1 short sentence",
  "ecosystem_impact": "1 short sentence",
  "summary": "2 short sentences",
  "action": "1 short practical action"
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
            {"role": "system", "content": "You are a strict JSON incident triage assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"].strip()
        return json.loads(content)
    except Exception as e:
        print("Featherless error:", e)
        return fallback_ai_analysis(issue_type, category, f"{latitude},{longitude}")

# -----------------------
# ElevenLabs TTS/STT
# -----------------------

def generate_voice(text, prefix="earth"):
    if not ELEVENLABS_API_KEY or not text.strip():
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
        print("ElevenLabs TTS error:", e)
        return ""

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
        print("ElevenLabs STT error:", e)
        return ""

# -----------------------
# Ticket creation helper
# -----------------------

def build_earth_voice_text(issue_type, risk_level, summary, action):
    return f"I detected {issue_type}. Risk level is {risk_level}. {summary} {action}"

# -----------------------
# Routes
# -----------------------

@app.get("/")
def home():
    return {"message": "PlanetSOS Guardian backend running"}

@app.get("/health")
def health():
    return {"status": "ok"}

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

@app.post("/report")
async def create_ticket(
    role: str = Form(...),
    latitude: str = Form(...),
    longitude: str = Form(...),
    address: str = Form(default=""),
    reporter_text: str = Form(default=""),
    reporter_transcript: str = Form(default=""),
    file: Optional[UploadFile] = File(default=None),
    voice_note: Optional[UploadFile] = File(default=None),
    authorization: Optional[str] = Header(None)
):
    if role != "reporter":
        raise HTTPException(status_code=400, detail="Only reporter can create a ticket")
    
    # Extract user_id from token if provided
    user_id = None
    if authorization and supabase_service.is_available():
        try:
            token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
            user = supabase_service.client.auth.get_user(token)
            if user.user:
                user_id = user.user.id
        except Exception as e:
            # If token is invalid, continue without user_id (anonymous report)
            pass

    image_url = ""
    issue_type = "environmental hazard"

    if file is not None:
        image_path = save_upload_file(file, "uploads")
        image_url = public_path("uploads", image_path)
        issue_type = detect_issue(file.filename or "")

    reporter_voice_url = ""
    if voice_note is not None:
        voice_path = save_upload_file(voice_note, "uploads_audio")
        reporter_voice_url = public_path("uploads_audio", voice_path)

        if not reporter_transcript.strip():
            reporter_transcript = transcribe_audio(voice_path)

    category = classify_category(issue_type)

    ai_result = analyze_issue_with_featherless(
        issue_type=issue_type,
        category=category,
        latitude=latitude,
        longitude=longitude,
        reporter_text=reporter_text,
        reporter_transcript=reporter_transcript
    )

    risk_level = ai_result["risk_level"]
    assigned_responder_type = assign_responder(issue_type, risk_level)

    earth_voice_text = build_earth_voice_text(
        issue_type,
        risk_level,
        ai_result["summary"],
        ai_result["action"]
    )
    earth_audio_url = generate_voice(earth_voice_text, "earth")

    ticket = {
        "ticket_id": str(uuid.uuid4()),
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "status": "open",
        "role": "reporter",
        "category": category,
        "issue_type": issue_type,
        "risk_level": risk_level,
        "health_concern": ai_result["health_concern"],
        "ecosystem_impact": ai_result["ecosystem_impact"],
        "summary": ai_result["summary"],
        "action": ai_result["action"],
        "assigned_responder_type": assigned_responder_type,
        "location": {
            "latitude": latitude,
            "longitude": longitude,
            "address": address
        },
        "reporter_text": reporter_text,
        "reporter_transcript": reporter_transcript,
        "reporter_voice_url": reporter_voice_url,
        "image_url": image_url,
        "earth_voice_text": earth_voice_text,
        "earth_audio_url": earth_audio_url,
        "responder_notes_text": "",
        "responder_transcript": "",
        "responder_voice_url": "",
        "responder_tts_url": "",
        "responder_type": ""
    }

    tickets = load_tickets()
    tickets.append(ticket)
    save_tickets(tickets)

    # Link ticket to user in Supabase if user is authenticated
    if user_id and supabase_service.is_available():
        supabase_service.link_ticket_to_user(ticket["ticket_id"], user_id)

    return ticket

@app.get("/ticket/{ticket_id}")
def get_ticket(ticket_id: str):
    tickets = load_tickets()
    for ticket in tickets:
        if ticket["ticket_id"] == ticket_id:
            return ticket
    raise HTTPException(status_code=404, detail="Ticket not found")

@app.get("/tickets")
def list_tickets(responder_type: Optional[str] = None, status: Optional[str] = None):
    tickets = load_tickets()

    if responder_type:
        tickets = [t for t in tickets if t["assigned_responder_type"] == responder_type]

    if status:
        tickets = [t for t in tickets if t["status"] == status]

    return {"tickets": tickets}

@app.post("/respond")
async def respond_to_ticket(
    ticket_id: str = Form(...),
    responder_type: str = Form(...),
    latitude: str = Form(...),
    longitude: str = Form(...),
    responder_text: str = Form(default=""),
    responder_transcript: str = Form(default=""),
    voice_note: Optional[UploadFile] = File(default=None),
    generate_spoken_reply: str = Form(default="false"),
    authorization: Optional[str] = Header(None)
):
    # Extract department_id from token if provided
    department_id = None
    if authorization and supabase_service.is_available():
        try:
            token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
            user = supabase_service.client.auth.get_user(token)
            if user.user:
                department_id = user.user.id
        except Exception as e:
            # If token is invalid, continue without department_id
            pass
    tickets = load_tickets()

    target_ticket = None
    for ticket in tickets:
        if ticket["ticket_id"] == ticket_id:
            target_ticket = ticket
            break

    if target_ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")

    responder_voice_url = target_ticket.get("responder_voice_url", "")

    if voice_note is not None:
        voice_path = save_upload_file(voice_note, "uploads_audio")
        responder_voice_url = public_path("uploads_audio", voice_path)

        if not responder_transcript.strip():
            responder_transcript = transcribe_audio(voice_path)

    responder_tts_url = target_ticket.get("responder_tts_url", "")

    if generate_spoken_reply.lower() == "true":
        speech_source_text = responder_text.strip() or responder_transcript.strip()
        if speech_source_text:
            responder_tts_url = generate_voice(speech_source_text, "responder")

    target_ticket["responder_type"] = responder_type
    target_ticket["responder_notes_text"] = responder_text
    target_ticket["responder_transcript"] = responder_transcript
    target_ticket["responder_voice_url"] = responder_voice_url
    target_ticket["responder_tts_url"] = responder_tts_url
    target_ticket["status"] = "responded"
    target_ticket["updated_at"] = now_iso()
    target_ticket["responder_location"] = {
        "latitude": latitude,
        "longitude": longitude
    }

    save_tickets(tickets)

    # Link ticket to department in Supabase if department is authenticated
    if department_id and supabase_service.is_available():
        supabase_service.link_ticket_to_department(ticket_id, department_id)

    return target_ticket