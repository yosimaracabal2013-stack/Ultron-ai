"""ULTRON v0.2 inference API."""

from pathlib import Path
import os
import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ai.tokenizer import CharTokenizer
from ai.model import UltronTransformer
from ai.mind import UltronMind

ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT = Path(os.getenv("ULTRON_CHECKPOINT", "/etc/secrets/ultron_v0_2.pt"))
TOKENIZER = Path(os.getenv("ULTRON_TOKENIZER", "/etc/secrets/tokenizer_v0_2.json"))

app = FastAPI(title="ULTRON v0.2 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

model = None
tokenizer = None
mind = UltronMind()

class ChatRequest(BaseModel):
    message: str
    max_tokens: int = 160
    temperature: float = 0.8

@app.on_event("startup")
def load_model():
    global model, tokenizer
    if not CHECKPOINT.exists() or not TOKENIZER.exists():
        raise RuntimeError(
            f"Missing ULTRON files. Expected {CHECKPOINT} and {TOKENIZER}."
        )
    tokenizer = CharTokenizer.load(TOKENIZER)
    checkpoint = torch.load(CHECKPOINT, map_location="cpu", weights_only=False)
    model = UltronTransformer(**checkpoint["config"])
    if checkpoint.get("format") == "ultron-int8-v1":
        state = {}
        for name, tensor in checkpoint["model_int8"].items():
            if name in checkpoint["scales"]:
                state[name] = tensor.float() * float(checkpoint["scales"][name])
            else:
                state[name] = tensor
        model.load_state_dict(state)
    else:
        model.load_state_dict(checkpoint["model"])
    model.eval()

@app.get("/")
def root():
    return {"name": "ULTRON", "model": "v0.2", "status": "online" if model is not None else "offline"}

@app.get("/state")
def state():
    return {"emotion": mind.emotion.snapshot(), "memory_items": len(mind.memory), "actions": mind.action_count}

@app.get("/health")
def health():
    return {"ok": model is not None, "model": "ULTRON v0.2"}

@app.post("/chat")
def chat(request: ChatRequest):
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="ULTRON model is not loaded.")
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message is empty.")
    if len(message) > 2000:
        raise HTTPException(status_code=400, detail="Message is too long.")
    try:
        mind.perceive(message)
        decision = mind.deliberate(message)
        prompt = f"User: {message}\nULTRON:"
        ids = torch.tensor([tokenizer.encode(prompt)], dtype=torch.long)
        with torch.no_grad():
            output = model.generate(
                ids,
                max(1, min(request.max_tokens, 300)),
                temperature=max(0.1, min(decision["temperature"] * request.temperature / 0.8, 1.5)),
            )[0].tolist()
        text = tokenizer.decode(output)
        reply = text[len(prompt):].strip()
        if not reply:
            reply = "I received your message, but I need more training before I can answer clearly."
        mind.remember(message, reply)
        mind.settle()
        return {"reply": reply, "action": decision["action"], "emotion": mind.emotion.snapshot()}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
