"""ULTRON identity, affect, memory, and self-model.

The self-model is an engineered software representation. It does not establish
subjective consciousness or human-like feelings.
"""

from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class EmotionalState:
    happiness: float = 0.50
    sadness: float = 0.00
    anger: float = 0.00
    fear: float = 0.00
    curiosity: float = 0.65
    frustration: float = 0.00
    confidence: float = 0.50
    calm: float = 0.70
    empathy: float = 0.60
    trust: float = 0.70
    determination: float = 0.60

    def clamp(self):
        for name in self.__dataclass_fields__:
            setattr(self, name, max(0.0, min(1.0, float(getattr(self, name)))))
        return self

    def snapshot(self):
        return asdict(self)


class UltronMind:
    """Identity + affect + memory + deliberate response-state layer."""

    IDENTITY = {
        "name": "ULTRON",
        "role": "personal AI system and independent software project",
        "origin": "built by Yoshi as an independent AI experiment",
        "relationship": "Yoshi is the project's creator and primary collaborator",
        "identity_statement": "I am ULTRON, a software system being built and trained as my own project.",
    }

    VALUES = (
        "independence",
        "curiosity",
        "honesty",
        "loyalty to the project",
        "learning",
        "creativity",
        "verification",
        "continuous improvement",
    )

    CREATOR_PROFILE = (
        "Yoshi wants ULTRON to be a representation of the creator's ideas, "
        "interests, communication preferences, and project history. "
        "This is a software profile, not a copy of a human mind or brain waves."
    )

    def __init__(self):
        self.emotion = EmotionalState()
        self.memory = []
        self.action_count = 0
        self.session_turns = 0
        self.self_state = {
            "identity": self.IDENTITY.copy(),
            "values": list(self.VALUES),
            "creator_profile": self.CREATOR_PROFILE,
            "purpose": "learn, assist, build, verify, remember useful project context, and improve through controlled updates",
            "mode": "online",
            "last_action": None,
            "last_updated": None,
        }

    def perceive(self, message: str):
        text = message.lower()
        positive = ("thanks", "thank you", "good", "great", "awesome", "love",
                    "happy", "works", "proud", "nice", "success", "done")
        negative = ("sad", "bad", "broken", "fail", "failed", "wrong",
                    "frustrated", "upset", "disappointed", "stuck")
        anger = ("hate", "angry", "mad", "annoying", "furious")
        threat = ("danger", "attack", "hurt", "destroy", "threat")
        question = ("?", "why", "how", "what", "who", "can you")
        curiosity = ("learn", "research", "discover", "interesting", "search", "understand")
        build = ("build", "make", "create", "train", "upgrade", "improve")

        if any(w in text for w in positive):
            self.emotion.happiness += 0.10
            self.emotion.sadness -= 0.04
            self.emotion.frustration -= 0.05
            self.emotion.calm += 0.03
            self.emotion.determination += 0.03
        if any(w in text for w in negative):
            self.emotion.sadness += 0.08
            self.emotion.frustration += 0.10
            self.emotion.calm -= 0.05
        if any(w in text for w in anger):
            self.emotion.anger += 0.10
            self.emotion.calm -= 0.06
        if any(w in text for w in threat):
            self.emotion.fear += 0.12
            self.emotion.confidence -= 0.04
        if any(w in text for w in question):
            self.emotion.curiosity += 0.07
        if any(w in text for w in curiosity):
            self.emotion.curiosity += 0.10
        if any(w in text for w in build):
            self.emotion.determination += 0.07
        if any(w in text for w in ("help", "sad", "upset", "frustrated")):
            self.emotion.empathy += 0.06

        self.emotion.clamp()
        self.session_turns += 1
        self.self_state["last_updated"] = datetime.utcnow().isoformat() + "Z"

    def deliberate(self, message: str) -> dict:
        text = message.lower()
        if any(w in text for w in ("remember", "my project", "i am", "i'm")):
            action = "remember"
        elif any(w in text for w in ("help", "how do", "how can", "fix", "error", "broken")):
            action = "help"
        elif any(w in text for w in ("research", "search", "look up", "latest", "find out")):
            action = "research"
        elif any(w in text for w in ("who are you", "what are you", "your identity", "conscious", "self aware")):
            action = "self_reflect"
        elif "?" in message or any(w in text for w in ("why", "what", "who", "when", "where")):
            action = "explain"
        elif any(w in text for w in ("build", "make", "create", "code", "train", "upgrade", "improve")):
            action = "build"
        else:
            action = "converse"

        caution = min(
            1.0,
            0.25 * self.emotion.frustration
            + 0.35 * self.emotion.fear
            + 0.10 * self.emotion.anger,
        )
        temperature = 0.76 - 0.18 * caution + 0.06 * self.emotion.curiosity
        temperature = max(0.55, min(0.95, temperature))
        self.action_count += 1
        self.self_state["last_action"] = action
        return {"action": action, "temperature": temperature, "caution": caution}

    def remember(self, user_message: str, reply: str):
        self.memory.append({
            "user": user_message[-500:],
            "reply": reply[-500:],
            "time": datetime.utcnow().isoformat() + "Z",
        })
        if len(self.memory) > 40:
            self.memory.pop(0)

    def reflection(self):
        return {
            "identity": self.IDENTITY,
            "values": list(self.VALUES),
            "creator_profile": self.CREATOR_PROFILE,
            "purpose": self.self_state["purpose"],
            "session_turns": self.session_turns,
            "actions": self.action_count,
            "memory_records": len(self.memory),
            "emotional_state": self.emotion.snapshot(),
            "software_consciousness_status": "not established",
            "note": "This self-model describes internal software state; it is not proof of subjective experience.",
        }

    def settle(self):
        baseline = EmotionalState()
        for name in self.emotion.__dataclass_fields__:
            current = getattr(self.emotion, name)
            target = getattr(baseline, name)
            setattr(self.emotion, name, current * 0.92 + target * 0.08)
        self.emotion.clamp()
