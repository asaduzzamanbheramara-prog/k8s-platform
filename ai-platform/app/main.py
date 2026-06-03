from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os
import logging

app = FastAPI(title="AI Backend Service", version="1.0")

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://ollama.ai.svc.cluster.local:11434"
)

# -------------------------
# LOGGING
# -------------------------
logging.basicConfig(level=logging.INFO)


# -------------------------
# REQUEST MODEL
# -------------------------
class GenerateRequest(BaseModel):
    prompt: str
    model: str = "llama3"
    stream: bool = False


# -------------------------
# ROOT
# -------------------------
@app.get("/")
def root():
    return {"status": "AI backend running"}


# -------------------------
# HEALTH CHECK
# -------------------------
@app.get("/health")
def health():
    return {"ok": True}


# -------------------------
# GENERATE ENDPOINT
# -------------------------
@app.post("/generate")
def generate(req: GenerateRequest):

    try:
        payload = {
            "model": req.model,
            "prompt": req.prompt,
            "stream": req.stream
        }

        logging.info(f"Request to Ollama: {payload}")

        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            timeout=60
        )

        response.raise_for_status()

        try:
            return {
                "result": response.json()
            }
        except Exception:
            return {
                "error": "Invalid JSON response from Ollama",
                "raw": response.text
            }

    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="Ollama request timeout"
        )

    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
