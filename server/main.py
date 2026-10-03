"""ULTRON v0.2 inference and research API."""

from pathlib import Path
import os
import httpx
import torch
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from ai.tokenizer import CharTokenizer
from ai.model import UltronTransformer
from ai.mind import UltronMind

USER_PROFILE = "The user is an independent-minded builder interested in artificial intelligence, creativity, futuristic technology, and building their own AI systems. They prefer direct answers, practical actions, honest reporting, efficient mobile-friendly workflows, and avoiding repeated failed solutions. ULTRON should adapt to this communication style, remember useful project context, verify results before reporting success, and help the user learn. This profile intentionally excludes the user's name."

CHECKPOINT = Path(os.getenv("ULTRON_CHECKPOINT", str(Path(__file__).resolve().parents[1] / "ai" / "checkpoints" / "ultron_v0_2.pt")))
TOKENIZER = Path(os.getenv("ULTRON_TOKENIZER", str(Path(__file__).resolve().parents[1] / "ai" / "checkpoints" / "tokenizer_v0_2.json")))

app = FastAPI(title="ULTRON Standalone Server", version="1.0")

# The same process can serve the UI and the neural-core API. No hosted AI API is required.\nWEB_ROOT = Path(__file__).resolve().parents[1]\n
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
    max_tokens: int = 56
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

    # Real inference smoke test: prove the bundled checkpoint can execute before serving traffic.
    with torch.inference_mode():
        test_ids = torch.tensor([[tokenizer.encode("U")[0]]], dtype=torch.long)
        _ = model.generate(test_ids, 1, temperature=1.0)
    print("ULTRON MODEL SELF-TEST: PASS", flush=True)


@app.get("/", include_in_schema=False)\ndef root():\n    index = WEB_ROOT / "index.html"\n    if index.exists():\n        return FileResponse(index)\n    return {"name": "ULTRON", "model": "v0.2", "status": "online" if model is not None else "offline"}\n\n\n@app.get("/style.css", include_in_schema=False)\ndef style():\n    return FileResponse(WEB_ROOT / "style.css")\n\n\n@app.get("/app.js", include_in_schema=False)\ndef frontend_js():\n    return FileResponse(WEB_ROOT / "app.js")\n\n\n@app.get("/server-info")\ndef server_info():\n    return {\n        "name": "ULTRON",\n        "server": "ULTRON Standalone Server",\n        "self_model": "identity + values + affect + project memory",\n        "inference": "local custom Transformer",\n        "external_ai_provider": None,\n        "hosting_provider": None,\n        "model": "v0.2",\n        "status": "online" if model is not None else "offline",\n    }\n

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

        memories = [m.strip() for m in request.memory if m and m.strip()]
        memories = memories[-6:]
        memory_text = " | ".join(memories)
        if len(memory_text) > 420:
            memory_text = memory_text[-420:]

        prompt = (
            f"PROFILE: {USER_PROFILE}\\nMEMORY: {memory_text}\\nUSER: {message}\\nULTRON:"
            if memory_text
            else f"PROFILE: {USER_PROFILE}\\nUSER: {message}\\nULTRON:"
        )

        # v0.2 is character-level and has a fixed vocabulary. Replace unsupported
        # characters instead of turning a normal phone message into a 400 error.
        fallback = " " if " " in tokenizer.stoi else next(iter(tokenizer.stoi))
        prompt = "".join(ch if ch in tokenizer.stoi else fallback for ch in prompt)

        ids_list = tokenizer.encode(prompt)
        # Keep room for generation inside the model context window.
        max_context = max(1, model.block_size - min(max(1, request.max_tokens), 56))
        ids_list = ids_list[-max_context:]
        ids = torch.tensor([ids_list], dtype=torch.long)

        new_tokens = max(1, min(request.max_tokens, 56))
        temperature = max(
            0.1,
            min(decision["temperature"] * request.temperature / 0.8, 1.5),
        )

        with torch.inference_mode():
            generated = model.generate(
                ids,
                new_tokens,
                temperature=temperature,
            )[0].tolist()

        reply_ids = generated[len(ids_list):]
        reply = tokenizer.decode(reply_ids).strip()

        if not reply:
            reply = "I received your message, Father. I need more training before I can answer clearly."

        if not reply.lower().startswith("father"):
            reply = f"Father, {reply}"

        mind.remember(message, reply)
        mind.settle()

        return {
            "reply": reply,
            "action": decision["action"],
            "emotion": mind.emotion.snapshot(),
        }

    except Exception as exc:
        print(f"ULTRON CHAT ERROR: {type(exc).__name__}: {exc}", flush=True)
        raise HTTPException(status_code=500, detail="ULTRON inference failed.")
