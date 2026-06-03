from fastapi import FastAPI
from pydantic import BaseModel
import requests

app = FastAPI()

OLLAMA_URL = "http://ollama.ai.svc.cluster.local:11434/api/generate"

class Prompt(BaseModel):
    prompt: str
    model: str = "deepseek-coder"

@app.post("/generate")
def generate(data: Prompt):

    payload = {
        "model": data.model,
        "prompt": data.prompt,
        "stream": False
    }

    r = requests.post(OLLAMA_URL, json=payload)

    return {
        "result": r.json().get("response", "")
    }
