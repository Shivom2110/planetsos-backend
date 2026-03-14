from fastapi import FastAPI, UploadFile, File

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
    analysis = analyze_issue_fake(pollution_type)
    audio_url = generate_voice_fake()

    return {
        "pollution_type": pollution_type,
        "severity": analysis["severity"],
        "summary": analysis["summary"],
        "action": analysis["action"],
        "audio_url": audio_url
    }