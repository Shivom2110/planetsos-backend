from fastapi import FastAPI, UploadFile, File
from dotenv import load_dotenv
import os
import requests
import json

# load environment variables
load_dotenv()

FEATHERLESS_API_KEY = os.getenv("FEATHERLESS_API_KEY")

app = FastAPI()


# -------------------------
# Fake label generator
# -------------------------
def get_labels_fake(filename):
    name = filename.lower()

    if "smoke" in name or "fire" in name:
        return ["Smoke", "Fire"]

    if "river" in name or "water" in name:
        return ["Plastic", "Bottle", "Water", "Garbage"]

    if "park" in name or "litter" in name or "trash" in name:
        return ["Trash", "Garbage", "Debris"]

    return ["Garbage"]


# -------------------------
# Convert labels → category
# -------------------------
def map_labels_to_category(labels):
    labels_lower = [label.lower() for label in labels]

    if "smoke" in labels_lower or "fire" in labels_lower:
        return "smoke / fire"

    if ("plastic" in labels_lower or "bottle" in labels_lower) and "water" in labels_lower:
        return "plastic waste near water"

    if "garbage" in labels_lower or "trash" in labels_lower or "debris" in labels_lower:
        return "trash dumping"

    return "general environmental hazard"


# -------------------------
# Detection pipeline
# -------------------------
def detect_issue(filename):
    labels = get_labels_fake(filename)
    return map_labels_to_category(labels)


# -------------------------
# Fallback analysis
# -------------------------
def analyze_issue_fallback(pollution_type):

    if pollution_type == "smoke / fire":
        return {
            "severity": "high",
            "summary": "Smoke and fire can damage ecosystems, harm wildlife, and reduce air quality.",
            "action": "Alert emergency responders and contain the affected area."
        }

    if pollution_type == "plastic waste near water":
        return {
            "severity": "high",
            "summary": "Plastic waste near water can harm aquatic life and contaminate ecosystems.",
            "action": "Organize immediate cleanup and monitor the area for repeated dumping."
        }

    if pollution_type == "trash dumping":
        return {
            "severity": "medium",
            "summary": "Trash dumping pollutes land and can damage nearby habitats.",
            "action": "Schedule cleanup and report illegal dumping if it continues."
        }

    return {
        "severity": "medium",
        "summary": "An environmental hazard was detected and may negatively affect the surrounding area.",
        "action": "Inspect the location and take appropriate action."
    }


# -------------------------
# Featherless AI analysis
# -------------------------
def analyze_issue_with_featherless(pollution_type):

    if not FEATHERLESS_API_KEY:
        return analyze_issue_fallback(pollution_type)

    prompt = f"""
You are an environmental risk analysis assistant.

Detected issue: {pollution_type}

Return ONLY valid JSON in this format:

{{
 "severity": "low or medium or high",
 "summary": "2 short sentences explaining environmental harm",
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
            {
                "role": "system",
                "content": "You explain environmental risks clearly and return strict JSON only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        data = response.json()

        content = data["choices"][0]["message"]["content"].strip()

        parsed = json.loads(content)

        return {
            "severity": parsed["severity"],
            "summary": parsed["summary"],
            "action": parsed["action"]
        }

    except Exception as e:
        print("Featherless error:", e)
        return analyze_issue_fallback(pollution_type)


# -------------------------
# Health route
# -------------------------
@app.get("/health")
def health():
    return {"message": "backend is working"}


# -------------------------
# Main analyze route
# -------------------------
@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):

    file_path = f"uploads/{file.filename}"

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    pollution_type = detect_issue(file.filename)

    analysis = analyze_issue_with_featherless(pollution_type)

    return {
        "pollution_type": pollution_type,
        "severity": analysis["severity"],
        "summary": analysis["summary"],
        "action": analysis["action"],
        "audio_url": ""
    }