from fastapi import FastAPI, UploadFile, File

app = FastAPI()


def get_labels_fake():
    return ["Smoke", "Fire"]


def map_labels_to_category(labels):
    labels_lower = [label.lower() for label in labels]

    if "smoke" in labels_lower or "fire" in labels_lower:
        return "smoke / fire"

    if ("plastic" in labels_lower or "bottle" in labels_lower) and "water" in labels_lower:
        return "plastic waste near water"

    if "garbage" in labels_lower or "trash" in labels_lower or "debris" in labels_lower:
        return "trash dumping"

    return "general environmental hazard"


def detect_issue_fake():
    labels = get_labels_fake()
    return map_labels_to_category(labels)


def analyze_issue_fake(pollution_type):
    return {
        "severity": "high",
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

    pollution_type = detect_issue_fake()
    analysis = analyze_issue_fake(pollution_type)
    audio_url = generate_voice_fake()

    return {
        "pollution_type": pollution_type,
        "severity": analysis["severity"],
        "summary": analysis["summary"],
        "action": analysis["action"],
        "audio_url": audio_url
    }