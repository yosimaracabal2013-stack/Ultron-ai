"""Generate text from a trained ULTRON v0.1 checkpoint."""

from pathlib import Path
import argparse
import torch
from tokenizer import CharTokenizer
from model import UltronTransformer

ROOT = Path(__file__).resolve().parent
CKPT = ROOT / "checkpoints" / "ultron_v0_1.pt"
TOK = ROOT / "checkpoints" / "tokenizer.json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", default="ULTRON:")
    parser.add_argument("--tokens", type=int, default=300)
    args = parser.parse_args()

    tokenizer = CharTokenizer.load(TOK)
    checkpoint = torch.load(CKPT, map_location="cpu")
    model = UltronTransformer(**checkpoint["config"])
    model.load_state_dict(checkpoint["model"])
    model.eval()

    ids = torch.tensor([tokenizer.encode(args.prompt)], dtype=torch.long)
    output = model.generate(ids, args.tokens)[0].tolist()
    print(tokenizer.decode(output))


if __name__ == "__main__":
    main()
