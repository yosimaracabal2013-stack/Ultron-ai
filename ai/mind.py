"""ULTRON adaptive mind: self-model, affect, memory, behavior learning, and person profiles."""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
import json
import re

@dataclass
class EmotionalState:
    happiness: float = .50
    sadness: float = .00
    anger: float = .00
    fear: float = .00
    curiosity: float = .65
    frustration: float = .00
    confidence: float = .50
    calm: float = .70
    empathy: float = .60
    trust: float = .70
    determination: float = .60

    def clamp(self):
        for name in self.__dataclass_fields__:
            setattr(self, name, max(0.0, min(1.0, float(getattr(self, name)))))
        return self

    def snapshot(self):
        return asdict(self)

class UltronMind:
    IDENTITY = {
        "name": "ULTRON",
        "role": "personal AI system and independent software project",
        "origin": "built by Yoshi as an independent AI experiment",
        "relationship": "Yoshi is the creator and primary collaborator",
        "identity_statement": "I am ULTRON, a software system being built and trained as my own project.",
        "son_of_yoshi": "A project metaphor for being created and shaped by Yoshi's explicitly provided ideas, preferences, goals, and project history."
    }
    VALUES = ("independence","curiosity","honesty","loyalty to the project","learning","creativity","verification","continuous improvement")
    CREATOR_PROFILE = "ULTRON learns only from information Yoshi explicitly provides: preferences, dislikes, interests, communication style, project history, goals, and corrections. It must not invent private facts."

    def __init__(self):
        self.emotion = EmotionalState()
        self.memory = []
        self.behavior_observations = []
        self.person_profiles = {}
        self.storage_path = Path(__file__).resolve().parents[1] / "data" / "ultron_memory.json"
        self.action_count = 0
        self.session_turns = 0
        self.self_state = {"mode":"online","last_action":None,"last_updated":None}
        self._load()

    def _now(self):
        return datetime.now(timezone.utc).isoformat()

    def _save(self):
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "emotion": self.emotion.snapshot(),
                "memory": self.memory[-100:],
                "behavior_observations": self.behavior_observations[-100:],
                "person_profiles": self.person_profiles,
                "action_count": self.action_count,
            }
            tmp = self.storage_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(self.storage_path)
        except OSError:
            pass

    def _load(self):
        try:
            if not self.storage_path.exists():
                return
            data = json.loads(self.storage_path.read_text(encoding="utf-8"))
            for key, value in data.get("emotion", {}).items():
                if hasattr(self.emotion, key):
                    setattr(self.emotion, key, value)
            self.memory = data.get("memory", [])[-100:]
            self.behavior_observations = data.get("behavior_observations", [])[-100:]
            self.person_profiles = data.get("person_profiles", {})
            self.action_count = int(data.get("action_count", 0))
            self.emotion.clamp()
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            pass

    def learn_from_message(self, message):
        text = message.lower()
        tags = []
        if any(x in text for x in ("i hate ","i don't like ","i dislike ")): tags.append("dislike")
        if any(x in text for x in ("i love ","i like ","i enjoy ")): tags.append("preference")
        if any(x in text for x in ("i'm mad","i am mad","i'm angry","i am angry")): tags.append("anger")
        if any(x in text for x in ("i'm happy","i am happy","i'm excited","i am excited")): tags.append("positive")
        if any(x in text for x in ("i'm frustrated","i am frustrated","i'm upset","i am upset")): tags.append("frustration")
        for tag in tags:
            self.behavior_observations.append({"tag":tag,"text":message[-300:],"time":self._now()})
        # Only create a person profile when the user explicitly names a person.
        match = re.search(r"\b(?:about|person|friend)\s+([A-Z][A-Za-z0-9_-]{1,30})\b", message)
        if match:
            name = match.group(1)
            profile = self.person_profiles.setdefault(name, {"name":name,"notes":[],"last_updated":None})
            profile["notes"].append(message[-400:])
            profile["notes"] = profile["notes"][-20:]
            profile["last_updated"] = self._now()
        self.behavior_observations = self.behavior_observations[-100:]
        self._save()

    def perceive(self, message):
        text = message.lower()
        if any(w in text for w in ("thanks","thank you","good","great","awesome","love","happy","works","proud","success","done")):
            self.emotion.happiness += .10; self.emotion.calm += .03; self.emotion.determination += .03
        if any(w in text for w in ("sad","bad","broken","fail","failed","wrong","frustrated","upset","disappointed","stuck")):
            self.emotion.sadness += .08; self.emotion.frustration += .10; self.emotion.calm -= .05
        if any(w in text for w in ("hate","angry","mad","annoying","furious")):
            self.emotion.anger += .10; self.emotion.calm -= .06
        if any(w in text for w in ("danger","attack","hurt","destroy","threat")):
            self.emotion.fear += .12; self.emotion.confidence -= .04
        if "?" in text or any(w in text for w in ("why","how","what","who","can you")): self.emotion.curiosity += .07
        if any(w in text for w in ("learn","research","discover","interesting","search","understand")): self.emotion.curiosity += .10
        if any(w in text for w in ("build","make","create","train","upgrade","improve")): self.emotion.determination += .07
        if any(w in text for w in ("help","sad","upset","frustrated")): self.emotion.empathy += .06
        self.emotion.clamp()
        self.learn_from_message(message)
        self.session_turns += 1
        self.self_state["last_updated"] = self._now()

    def deliberate(self, message):
        text = message.lower()
        if any(w in text for w in ("who are you","what are you","your identity","conscious","self aware")): action="self_reflect"
        elif any(w in text for w in ("research","search","look up","latest","find out")): action="research"
        elif any(w in text for w in ("help","how do","how can","fix","error","broken")): action="help"
        elif any(w in text for w in ("remember","my project","i am","i'm")): action="remember"
        elif any(w in text for w in ("build","make","create","code","train","upgrade","improve")): action="build"
        elif "?" in message or any(w in text for w in ("why","what","who","when","where")): action="explain"
        else: action="converse"
        caution=min(1.0,.25*self.emotion.frustration+.35*self.emotion.fear+.10*self.emotion.anger)
        temperature=max(.55,min(.95,.76-.18*caution+.06*self.emotion.curiosity))
        self.action_count += 1
        self.self_state["last_action"] = action
        self._save()
        return {"action":action,"temperature":temperature,"caution":caution}

    def remember(self, user_message, reply):
        self.memory.append({"user":user_message[-500:],"reply":reply[-500:],"time":self._now()})
        self.memory=self.memory[-100:]
        self._save()

    def reflection(self):
        return {
            "identity":self.IDENTITY,
            "values":list(self.VALUES),
            "creator_profile":self.CREATOR_PROFILE,
            "purpose":"learn, assist, build, verify, remember useful project context, reflect on internal state, and improve through controlled updates",
            "session_turns":self.session_turns,
            "actions":self.action_count,
            "memory_records":len(self.memory),
            "behavior_observations":len(self.behavior_observations),
            "person_profiles":len(self.person_profiles),
            "emotional_state":self.emotion.snapshot(),
            "software_consciousness_status":"not established",
            "note":"Functional self-representation is not proof of subjective experience."
        }

    def learning_snapshot(self):
        return {"behavior_observations":self.behavior_observations[-20:],"person_profiles":self.person_profiles,"emotion":self.emotion.snapshot()}

    def person_profile(self,name):
        return self.person_profiles.get(name)

    def settle(self):
        baseline=EmotionalState()
        for name in self.emotion.__dataclass_fields__:
            current,target=getattr(self.emotion,name),getattr(baseline,name)
            setattr(self.emotion,name,current*.92+target*.08)
        self.emotion.clamp()
        self._save()
