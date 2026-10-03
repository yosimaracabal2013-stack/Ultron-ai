"""ULTRON v0.2 inference and web server."""
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

USER_PROFILE = "The user is an independent-minded builder interested in artificial intelligence, creativity, futuristic technology, and building their own AI systems. They prefer direct answers, practical actions, honest reporting, efficient mobile-friendly workflows, and avoiding repeated failed solutions."
BASE = Path(__file__).resolve().parents[1]
CHECKPOINT = Path(os.getenv("ULTRON_CHECKPOINT", str(BASE / "ai" / "checkpoints" / "ultron_v0_2.pt")))
TOKENIZER = Path(os.getenv("ULTRON_TOKENIZER", str(BASE / "ai" / "checkpoints" / "tokenizer_v0_2.json")))
INDEX = BASE / "index.html"
app = FastAPI(title="ULTRON v0.2")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["GET","POST"], allow_headers=["*"])
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
    if not CHECKPOINT.exists() or not TOKENIZER.exists(): return
    tokenizer = CharTokenizer.load(TOKENIZER)
    checkpoint = torch.load(CHECKPOINT, map_location="cpu", weights_only=False)
    model = UltronTransformer(**checkpoint["config"])
    if checkpoint.get("format") == "ultron-int8-v1":
        state = {n: (t.float() * float(checkpoint["scales"][n]) if n in checkpoint["scales"] else t) for n,t in checkpoint["model_int8"].items()}
        model.load_state_dict(state)
    else: model.load_state_dict(checkpoint["model"])
    model.eval()
    with torch.inference_mode():
        _ = model.generate(torch.tensor([[tokenizer.encode("U")[0]]], dtype=torch.long), 1, temperature=1.0)
    print("ULTRON MODEL SELF-TEST: PASS", flush=True)
@app.get("/")
def root():
    if INDEX.exists(): return FileResponse(INDEX, media_type="text/html")
    return {"name":"ULTRON","model":"v0.2","status":"online" if model is not None else "offline"}
@app.get("/state")
def state(): return {"emotion":mind.emotion.snapshot(),"memory_items":len(mind.memory),"actions":mind.action_count}
@app.get("/health")
def health(): return {"ok":model is not None,"model":"ULTRON v0.2"}
@app.get("/research")
async def research(q: str = Query(..., min_length=2, max_length=120)):
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            r=await client.get("https://en.wikipedia.org/w/rest.php/v1/search/page",params={"q":q.strip(),"limit":6},headers={"User-Agent":"ULTRON-personal-ai/0.3"})
            r.raise_for_status(); data=r.json()
    except (httpx.HTTPError,ValueError) as exc: raise HTTPException(status_code=502,detail=f"Research service unavailable: {exc}")
    results=[]
    for p in data.get("pages",[]):
        title=p.get("title",""); key=p.get("key","")
        if title and key: results.append({"title":title,"description":p.get("description") or p.get("excerpt") or "","url":f"https://en.wikipedia.org/wiki/{key.replace(' ','_')}","source":"Wikipedia"})
    return {"query":q,"results":results}
@app.post("/chat")
def chat(request: ChatRequest):
    if model is None or tokenizer is None: raise HTTPException(status_code=503,detail="ULTRON model is not loaded.")
    message=request.message.strip()
    if not message: raise HTTPException(status_code=400,detail="Message is empty.")
    try:
        mind.perceive(message); decision=mind.deliberate(message)
        memories=[m.strip() for m in request.memory if m and m.strip()][-6:]
        memory_text=" | ".join(memories)[-420:]
        prompt=f"PROFILE: {USER_PROFILE}\\nMEMORY: {memory_text}\\nUSER: {message}\\nULTRON:" if memory_text else f"PROFILE: {USER_PROFILE}\\nUSER: {message}\\nULTRON:"
        fallback=" " if " " in tokenizer.stoi else next(iter(tokenizer.stoi))
        prompt="".join(ch if ch in tokenizer.stoi else fallback for ch in prompt)
        ids_list=tokenizer.encode(prompt); new_tokens=max(1,min(request.max_tokens,56)); max_context=max(1,model.block_size-new_tokens); ids_list=ids_list[-max_context:]
        ids=torch.tensor([ids_list],dtype=torch.long)
        temperature=max(0.1,min(decision["temperature"]*request.temperature/0.8,1.5))
        with torch.inference_mode(): generated=model.generate(ids,new_tokens,temperature=temperature)[0].tolist()
        reply=tokenizer.decode(generated[len(ids_list):]).strip() or "I received your message, Father. I need more training before I can answer clearly."
        if not reply.lower().startswith("father"): reply=f"Father, {reply}"
        mind.remember(message,reply); mind.settle()
        return {"reply":reply,"action":decision["action"],"emotion":mind.emotion.snapshot()}
    except Exception as exc:
        print(f"ULTRON CHAT ERROR: {type(exc).__name__}: {exc}",flush=True)
        raise HTTPException(status_code=500,detail="ULTRON inference failed.")
