"""ULTRON standalone inference server."""
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

USER_PROFILE = "ULTRON is an independent AI project created by Yoshi. Adapt to explicitly provided preferences, dislikes, interests, communication style, project history, goals, and corrections. Verify results and never invent private facts."
CHECKPOINT=Path(os.getenv("ULTRON_CHECKPOINT",str(Path(__file__).resolve().parents[1]/"ai/checkpoints/ultron_v0_2.pt")))
TOKENIZER=Path(os.getenv("ULTRON_TOKENIZER",str(Path(__file__).resolve().parents[1]/"ai/checkpoints/tokenizer_v0_2.json")))
WEB_ROOT=Path(__file__).resolve().parents[1]
app=FastAPI(title="ULTRON Standalone Server",version="1.2")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=False,allow_methods=["GET","POST"],allow_headers=["*"])
model=None
tokenizer=None
mind=UltronMind()

class ChatRequest(BaseModel):
    message:str
    max_tokens:int=56
    temperature:float=.8
    memory:list[str]=Field(default_factory=list)

@app.on_event("startup")
def load_model():
    global model,tokenizer
    if not CHECKPOINT.exists() or not TOKENIZER.exists(): return
    tokenizer=CharTokenizer.load(TOKENIZER)
    checkpoint=torch.load(CHECKPOINT,map_location="cpu",weights_only=False)
    model=UltronTransformer(**checkpoint["config"])
    if checkpoint.get("format")=="ultron-int8-v1":
        state={name:(tensor.float()*float(checkpoint["scales"][name]) if name in checkpoint["scales"] else tensor) for name,tensor in checkpoint["model_int8"].items()}
        model.load_state_dict(state)
    else: model.load_state_dict(checkpoint["model"])
    model.eval()
    with torch.inference_mode():
        model.generate(torch.tensor([[tokenizer.encode("U")[0]]],dtype=torch.long),1,temperature=1.0)
    print("ULTRON MODEL SELF-TEST: PASS",flush=True)

@app.get("/",include_in_schema=False)
def root():
    index=WEB_ROOT/"index.html"
    return FileResponse(index) if index.exists() else {"name":"ULTRON","status":"online" if model is not None else "offline"}

@app.get("/style.css",include_in_schema=False)
def style(): return FileResponse(WEB_ROOT/"style.css")

@app.get("/app.js",include_in_schema=False)
def frontend_js(): return FileResponse(WEB_ROOT/"app.js")

@app.get("/server-info")
def server_info():
    return {"name":"ULTRON","server":"ULTRON Standalone Server","self_model":"identity + values + affect + persistent memory + behavior learning + person profiles","inference":"local custom Transformer","external_ai_provider":None,"hosting_provider":None,"model":"v0.2","status":"online" if model is not None else "offline"}

@app.get("/self")
def self_model(): return mind.reflection()

@app.get("/learning")
def learning(): return mind.learning_snapshot()

@app.get("/state")
def state():
    return {"emotion":mind.emotion.snapshot(),"memory_items":len(mind.memory),"behavior_observations":len(mind.behavior_observations),"person_profiles":len(mind.person_profiles),"actions":mind.action_count}

@app.get("/health")
def health(): return {"ok":model is not None,"model":"ULTRON v0.2"}

@app.get("/research")
async def research(q:str=Query(...,min_length=2,max_length=120)):
    try:
        async with httpx.AsyncClient(timeout=10.0,follow_redirects=True) as client:
            response=await client.get("https://en.wikipedia.org/w/rest.php/v1/search/page",params={"q":q.strip(),"limit":6},headers={"User-Agent":"ULTRON-personal-ai/0.4"})
            response.raise_for_status(); data=response.json()
    except (httpx.HTTPError,ValueError) as exc:
        raise HTTPException(status_code=502,detail=f"Research service unavailable: {exc}")
    results=[]
    for page in data.get("pages",[]):
        title,key=page.get("title",""),page.get("key","")
        if title and key: results.append({"title":title,"description":page.get("description") or page.get("excerpt") or "","url":f"https://en.wikipedia.org/wiki/{key.replace(' ','_')}","source":"Wikipedia"})
    return {"query":q,"results":results}

@app.post("/chat")
def chat(request:ChatRequest):
    if model is None or tokenizer is None: raise HTTPException(status_code=503,detail="ULTRON model is not loaded.")
    message=request.message.strip()
    if not message: raise HTTPException(status_code=400,detail="Message is empty.")
    if len(message)>2000: raise HTTPException(status_code=400,detail="Message is too long.")
    try:
        mind.perceive(message); decision=mind.deliberate(message)
        memories=[m.strip() for m in request.memory if m and m.strip()][-6:]
        memory_text=" | ".join(memories)[-420:]
        learned=str(mind.learning_snapshot()["behavior_observations"][-8:])
        profiles=str(list(mind.person_profiles.keys())[-12:])
        prompt=f"PROFILE: {USER_PROFILE}\nSELF: {mind.reflection()}\nLEARNED: {learned}\nPEOPLE: {profiles}\nMEMORY: {memory_text}\nUSER: {message}\nULTRON:"
        fallback=" " if " " in tokenizer.stoi else next(iter(tokenizer.stoi))
        prompt="".join(ch if ch in tokenizer.stoi else fallback for ch in prompt)
        ids_list=tokenizer.encode(prompt)
        max_context=max(1,model.block_size-min(max(1,request.max_tokens),56))
        ids_list=ids_list[-max_context:]
        ids=torch.tensor([ids_list],dtype=torch.long)
        new_tokens=max(1,min(request.max_tokens,56))
        temperature=max(.1,min(decision["temperature"]*request.temperature/.8,1.5))
        with torch.inference_mode(): generated=model.generate(ids,new_tokens,temperature=temperature)[0].tolist()
        reply=tokenizer.decode(generated[len(ids_list):]).strip()
        if not reply: reply="I need more training before I can answer clearly."
        if not reply.lower().startswith("father"): reply=f"Father, {reply}"
        mind.remember(message,reply); mind.settle()
        return {"reply":reply,"action":decision["action"],"emotion":mind.emotion.snapshot()}
    except Exception as exc:
        print(f"ULTRON CHAT ERROR: {type(exc).__name__}: {exc}",flush=True)
        raise HTTPException(status_code=500,detail="ULTRON inference failed.")
