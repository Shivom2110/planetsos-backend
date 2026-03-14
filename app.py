from fastapi import FastAPI, UploadFile, File
from dotenv import load_dotenv
import os
import requests

load_dotenv()

FEATHERLESS_API_KEY = os.getenv("FEATHERLESS_API_KEY")

app = FastAPI()


def get_labels_fake(filename):
    name = filename.lower()

    if "smoke" in name or "fire" in name:
        return ["Smoke", "Fire"]

    if "river" in name or "water" in name:
        return ["Plastic", "Bottle", "Water", "Garbage"]

    if "park" in name or "litter" in name or "trash" in name:
        return ["Trash", "Garbage", "Debris"]

    return ["Garbage"]


def map_labels_to_category(labels):
    labels_lower = [label.lower() for label in labels]

    if "smoke" in labels_lower or "fire" in labels_lower:
        return "smoke / fire"

    if ("plastic" in labels_lower or "bottle" in labels_lower) and "water" in labels_lower:
        return "plastic waste near water"

    if "garbage" in labels_lower or "trash" in labels_lower or "debris" in labels_lower:
        return "trash dumping"

    return "general environmental hazard"


def detect_issue_fake(filename):
    labels = get_labels_fake(filename)
    return map_labels_to_category(labels)


def analyze_issue_fake(pollution_type):
    if pollution_type == "smoke / fire":
        severity = "high"
    elif pollution_type == "plastic waste near water":
        severity = "high"
    elif pollution_type == "trash dumping":
        severity = "medium"
    else:
        severity = "medium"

    return {
        "severity": severity,
        "summary": f"{pollution_type.capitalize()} was detected and may harm the environment.",
        "action": "Organize cleanup and report repeated dumping."
    }


def generate_voice_fake():
    return ""


@app.get("/health")
def health():
    return {"message": "backend is working"}


@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    file_path = f"uploads/{file.filename}"

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    pollution_type = detect_issue_fake(file.filename)
    analysis = analyze_issue_with_featherless(pollution_type)
    audio_url = generate_voice_fake()

    return {
        "pollution_type": pollution_type,
        "severity": analysis["severity"],
        "summary": analysis["summary"],
        "action": analysis["action"],
        "audio_url": audio_url
    }
def analyze_issue_with_featherless(pollution_type):

    if not FEATHERLESS_API_KEY:
        return analyze_issue_fallback(pollution_type)

    prompt = f"""
You are an environmental risk analysis assistant.

Detected issue: {pollution_type}

Explain the environmental impact in 2 short sentences and suggest one action.
"""

    url = "https://api.featherless.ai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {FEATHERLESS_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "meta-llama/Meta-Llama-3.1-8B-Instruct",
        "messages": [
            {"role": "system", "content": "You explain environmental risks clearly."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        data = response.json()

        content = data["choices"][0]["message"]["content"]

        return {
            "severity": "medium",
            "summary": content,
            "action": "Review and respond appropriately."
        }

    except Exception as e:
        print("Featherless error:", e)
        return analyze_issue_fallback(pollution_type)