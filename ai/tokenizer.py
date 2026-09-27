"""A tiny character-level tokenizer for ULTRON v0.1."""

class CharTokenizer:
    def __init__(self, text: str):
        chars = sorted(set(text))
        self.stoi = {ch: i for i, ch in enumerate(chars)}
        self.itos = {i: ch for ch, i in self.stoi.items()}

    @property
    def vocab_size(self) -> int:
        return len(self.stoi)

    def encode(self, text: str) -> list[int]:
        unknown = [ch for ch in text if ch not in self.stoi]
        if unknown:
            raise ValueError(f"Text contains characters not in tokenizer vocabulary: {unknown[:5]}")
        return [self.stoi[ch] for ch in text]

    def decode(self, ids: list[int]) -> str:
        return "".join(self.itos[i] for i in ids)

    def save(self, path: str) -> None:
        import json
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"stoi": self.stoi}, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: str):
        import json
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        obj = cls("")
        obj.stoi = {k: int(v) for k, v in data["stoi"].items()}
        obj.itos = {i: ch for ch, i in obj.stoi.items()}
        return obj
