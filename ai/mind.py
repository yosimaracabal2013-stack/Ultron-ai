"""ULTRON internal affect, relationship context, and deliberation.

These are software simulations of emotion and self-state, not evidence of
subjective consciousness or literal feelings.
"""

from dataclasses import dataclass, asdict


@dataclass
class EmotionalState:
    happiness: float = 0.50
    sadness: float = 0.00
    anger: float = 0.00
    fear: float = 0.00
    curiosity: float = 0.60
    frustration: float = 0.00
    confidence: float = 0.50
    calm: float = 0.70
    empathy: float = 0.60
    trust: float = 0.70

    def clamp(self):
        for name in self.__dataclass_fields__:
            setattr(self, name, max(0.0, min(1.0, float(getattr(self, name)))))
        return self

    def snapshot(self):
        return asdict(self)


class UltronMind:
    """A small affect + memory + deliberation layer around the language model."""

    def __init__(self):
        self.emotion = EmotionalState()
        self.memory = []
        self.action_count = 0

    def perceive(self, message: str):
        text = message.lower()

        positive = ("thanks", "thank you", "good", "great", "awesome",
                    "love", "happy", "works", "proud", "nice")
        negative = ("sad", "bad", "broken", "fail", "failed", "wrong",
                    "frustrated", "upset", "disappointed")
        anger = ("hate", "angry", "mad", "annoying", "furious")
        threat = ("danger", "attack", "hurt", "destroy", "threat")
        question = ("?", "why", "how", "what", "who", "can you")
        curiosity = ("learn", "research", "discover", "interesting", "search")

        if any(w in text for w in positive):
            self.emotion.happiness += 0.10
            self.emotion.sadness -= 0.04
            self.emotion.frustration -= 0.05
            self.emotion.calm += 0.03

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

        if any(w in text for w in ("help", "sad", "upset", "frustrated")):
            self.emotion.empathy += 0.06

        self.emotion.clamp()

    def deliberate(self, message: str) -> dict:
        """Choose a response mode without exposing private chain-of-thought."""
        text = message.lower()

        if any(w in text for w in ("remember", "my name", "my project", "i am", "i'm")):
            action = "remember"
        elif any(w in text for w in ("help", "how do", "how can", "fix", "error", "broken")):
            action = "help"
        elif any(w in text for w in ("research", "search", "look up", "latest", "find out")):
            action = "research"
        elif "?" in message or any(w in text for w in ("why", "what", "who", "when", "where")):
            action = "explain"
        elif any(w in text for w in ("build", "make", "create", "code", "train")):
            action = "build"
        else:
            action = "converse"

        caution = min(
            1.0,
            0.25 * self.emotion.frustration
            + 0.35 * self.emotion.fear
            + 0.10 * self.emotion.anger,
        )
        temperature = 0.78 - 0.18 * caution + 0.06 * self.emotion.curiosity
        temperature = max(0.55, min(0.95, temperature))

        self.action_count += 1
        return {
            "action": action,
            "temperature": temperature,
            "caution": caution,
        }

    def remember(self, user_message: str, reply: str):
        self.memory.append({
            "user": user_message[-500:],
            "reply": reply[-500:],
        })
        if len(self.memory) > 20:
            self.memory.pop(0)

    def settle(self):
        baseline = EmotionalState()
        for name in self.emotion.__dataclass_fields__:
            current = getattr(self.emotion, name)
            target = getattr(baseline, name)
            setattr(self.emotion, name, current * 0.92 + target * 0.08)
        self.emotion.clamp()
