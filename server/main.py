"""ULTRON v0.2 inference and research API."""

from pathlib import Path
import os
import httpx
import torch
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from ai.tokenizer import CharTokenizer
from ai.model import UltronTransformer
from ai.mind import UltronMind

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
# Keep CPU inference responsive on small hosted instances.
torch.set_num_threads(max(1, min(4, os.cpu_count() or 1)))


class ChatRequest(BaseModel):
    message: str
    max_tokens: int = 48
    temperature: float = 0.8
    memory: list[str] = Field(default_factory=list)


@app.on_event("startup")
def load_model():
    global model, tokenizer
    if not CHECKPOINT.exists() or not TOKENIZER.exists():
        model = None
        tokenizer = None
        return
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
    return {
        "name": "ULTRON",
        "model": "v0.2",
        "status": "online" if model is not None else "offline",
    }


@app.get("/state")
def state():
    return {
        "emotion": mind.emotion.snapshot(),
        "memory_items": len(mind.memory),
        "actions": mind.action_count,
    }


@app.get("/health")
def health():
    return {"ok": model is not None, "model": "ULTRON v0.2"}


@app.get("/research")
async def research(q: str = Query(..., min_length=2, max_length=120)):
    """Search Wikipedia's public API and return concise source cards."""
    query = q.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Research query is empty.")

    url = "https://en.wikipedia.org/w/rest.php/v1/search/page"
    params = {"q": query, "limit": 6}
    headers = {"User-Agent": "ULTRON-personal-ai/0.3"}

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"Research service unavailable: {exc}")

    results = []
    for page in data.get("pages", []):
        title = page.get("title", "")
        description = page.get("description") or page.get("excerpt") or ""
        key = page.get("key", "")
        if not title or not key:
            continue
        results.append({
            "title": title,
            "description": description,
            "url": f"https://en.wikipedia.org/wiki/{key.replace(' ', '_')}",
            "source": "Wikipedia",
        })

    return {"query": query, "results": results}


def _local_reply(message: str, memories: list[str]) -> str:
    """Deterministic local response layer; never exposes untrained character-model gibberish."""
    import re

    text = message.strip()
    low = text.lower()
    clean = re.sub(r"[^a-z0-9?'+*/%. -]", "", low).strip()

    # Small, predictable arithmetic capability.
    math_match = re.fullmatch(r"(?:what is |calculate |solve )?(-?\d+(?:\.\d+)?)\s*([+*/%]|\bx\b|\*\*|\-|\bplus\b|\bminus\b|\btimes\b|\bdivided by\b)\s*(-?\d+(?:\.\d+)?)\??", clean)
    if math_match:
        a, op, b = math_match.groups()
        x, y = float(a), float(b)
        op = op.strip()
        try:
            result = {"+": lambda: x+y, "plus": lambda: x+y,
                      "-": lambda: x-y, "minus": lambda: x-y,
                      "*": lambda: x*y, "x": lambda: x*y,
                      "times": lambda: x*y, "/": lambda: x/y,
                      "divided by": lambda: x/y, "%": lambda: x%y,
                      "**": lambda: x**y}[op]()
            rendered = str(int(result)) if result.is_integer() else f"{result:.6g}"
            return f"The answer is {rendered}."
        except (ZeroDivisionError, OverflowError):
            return "That calculation is undefined. Check the numbers and try again."

    if re.search(r"\b(hi|hey|hello|yo|sup)\b", low) and len(low.split()) <= 7:
        return "Hello, Father. I'm online and ready. What are we working on?"
    if any(k in low for k in ("who are you", "what are you", "introduce yourself")):
        return "I'm ULTRON, your personal AI project. I can chat, use the notes you provide as context, help plan and debug projects, and run a few reliable built-in tasks. My language model is still under development, so I won't pretend to know things I can't answer."
    if any(k in low for k in ("what can you do", "your capabilities", "help me", "how can you help")):
        return "I can help plan and troubleshoot your projects, explain concepts, perform basic arithmetic, and use the memories and profile you send with a message. Research is available in the Research module. My independent language model still needs proper training, so I will say when I don't know rather than invent an answer."
    if any(k in low for k in ("how are you", "how do you feel", "your mood")):
        return "Systems are online, Father. My status indicators are software simulations, not human feelings. I'm ready to help."
    if any(k in low for k in ("remember", "what do you know about me", "my profile", "what do you know")):
        if memories:
            return "Here's the context available to me right now: " + " | ".join(memories[-4:])
        return "I don't have any saved context attached to this message yet. Add notes in Memory & Knowledge or your Father Profile to give me context."
    if any(k in low for k in ("ultron project", "our project", "the website", "the app", "the site")):
        return "The ULTRON project has a browser interface, a separate API, local browser memories, a profile, voice controls, and a small experimental Transformer. The current priority is making replies reliable and improving the interface. The small Transformer is not yet capable of dependable open-ended conversation."
    if any(k in low for k in ("why", "how", "what", "who", "when", "where")):
        return "I don't have a reliable trained answer for that yet, Father. I won't generate random text and pass it off as intelligence. Try the Research module for a source-backed lookup, or ask me to break the question into steps."
    if any(k in low for k in ("thank", "nice", "good job", "works")):
        return "Acknowledged, Father. I'll keep the next step clear and practical."
    return "I'm listening, Father. My independent language model is still being trained, so I don't want to invent an answer. Give me a specific task or use the Research module when you need factual information."


@app.post("/chat")
def chat(request: ChatRequest):
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message is empty.")
    if len(message) > 2000:
        raise HTTPException(status_code=400, detail="Message is too long.")

    try:
        mind.perceive(message)
        decision = mind.deliberate(message)
        memories = [m.strip() for m in request.memory if m and m.strip()][-6:]
        reply = _local_reply(message, memories)
        mind.remember(message, reply)
        mind.settle()
        return {
            "reply": reply,
            "action": decision["action"],
            "emotion": mind.emotion.snapshot(),
            "engine": "ULTRON local response layer",
            "model_ready": model is not None,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
