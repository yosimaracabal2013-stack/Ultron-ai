"""Train ULTRON's tiny Transformer from scratch."""

from pathlib import Path
import json
import torch
from tokenizer import CharTokenizer
from model import UltronTransformer

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "train.txt"
OUT = ROOT / "checkpoints"
OUT.mkdir(exist_ok=True)

# FAST TEST SETTINGS: this is only to prove the training pipeline works.
BLOCK_SIZE = 64
BATCH_SIZE = 16
N_EMBD = 64
N_HEAD = 4
N_LAYER = 2
DROPOUT = 0.1
STEPS = 100
LEARNING_RATE = 3e-4
SAVE_EVERY = 25


def get_batch(data, device):
    ix = torch.randint(0, len(data) - BLOCK_SIZE - 1, (BATCH_SIZE,))
    x = torch.stack([data[i:i + BLOCK_SIZE] for i in ix])
    y = torch.stack([data[i + 1:i + BLOCK_SIZE + 1] for i in ix])
    return x.to(device), y.to(device)


def save_checkpoint(model, tokenizer, device, step):
    checkpoint = {
        "model": model.state_dict(),
        "config": {
            "vocab_size": tokenizer.vocab_size,
            "block_size": BLOCK_SIZE,
            "n_embd": N_EMBD,
            "n_head": N_HEAD,
            "n_layer": N_LAYER,
            "dropout": DROPOUT,
        },
    }
    torch.save(checkpoint, OUT / "ultron_v0_1.pt")
    (OUT / "training_info.json").write_text(
        json.dumps({"steps": step, "device": device, "mode": "fast-test"}, indent=2),
        encoding="utf-8",
    )
    print(f"CHECKPOINT SAVED at step {step}: {OUT / 'ultron_v0_1.pt'}", flush=True)


def main():
    torch.manual_seed(42)
    text = DATA.read_text(encoding="utf-8")
    if len(text) < BLOCK_SIZE + 2:
        raise ValueError("Training text is too small for the configured block size.")

    tokenizer = CharTokenizer(text)
    ids = torch.tensor(tokenizer.encode(text), dtype=torch.long)

    split = int(0.8 * len(ids))
    if len(ids) - split < BLOCK_SIZE + 2:
        split = len(ids) - (BLOCK_SIZE + 2)
    if split < BLOCK_SIZE + 2:
        raise ValueError("Training text is too small for both train and validation windows.")
    train_data, val_data = ids[:split], ids[split:]

    tokenizer.save(OUT / "tokenizer.json")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = UltronTransformer(
        tokenizer.vocab_size,
        block_size=BLOCK_SIZE,
        n_embd=N_EMBD,
        n_head=N_HEAD,
        n_layer=N_LAYER,
        dropout=DROPOUT,
    ).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE)

    print(f"ULTRON v0.1 FAST TEST | device={device} | vocab={tokenizer.vocab_size}", flush=True)
    print(f"Training for only {STEPS} steps...", flush=True)

    for step in range(1, STEPS + 1):
        model.train()
        xb, yb = get_batch(train_data, device)
        _, loss = model(xb, yb)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()

        if step == 1 or step % 10 == 0:
            model.eval()
            with torch.no_grad():
                vx, vy = get_batch(val_data, device)
                _, vloss = model(vx, vy)
            print(
                f"step {step:3d}/{STEPS} | train {loss.item():.4f} | val {vloss.item():.4f}",
                flush=True,
            )

        if step % SAVE_EVERY == 0:
            save_checkpoint(model, tokenizer, device, step)

    save_checkpoint(model, tokenizer, device, STEPS)
    print("FAST TEST COMPLETE.", flush=True)


if __name__ == "__main__":
    main()
