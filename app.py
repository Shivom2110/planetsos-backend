from fastapi import FastAPI, UploadFile, File
import os

app = FastAPI()

@app.get("/health")
def health():
    return {"message": "backend is working"}

@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    file_path = f"uploads/{file.filename}"

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    return {
        "pollution_type": "plastic waste near water",
        "severity": "high",
        "summary": "Plastic waste was detected near water and may harm aquatic life.",
        "action": "Organize cleanup and report repeated dumping.",
        "audio_url": ""
    }