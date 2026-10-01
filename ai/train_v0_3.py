"""ULTRON v0.3 training pipeline.

Designed for Google Colab GPU training. This keeps the custom ULTRON
Transformer architecture, but trains substantially longer and records
validation loss and configuration so runs can be compared.
"""
from pathlib import Path
import json
import os
import time
import torch
from tokenizer import CharTokenizer
from model import UltronTransformer

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "train.txt"
DIALOGUE = ROOT / "data" / "dialogue_v0_3.txt"
OUT = ROOT / "checkpoints"
OUT.mkdir(exist_ok=True)

# Still intentionally compact so ULTRON remains a project-built model.
BLOCK_SIZE = 192
BATCH_SIZE = 32
N_EMBD = 96
N_HEAD = 4
N_LAYER = 4
DROPOUT = 0.10

GPU_STEPS = int(os.environ.get("ULTRON_GPU_STEPS", "5000"))
CPU_STEPS = int(os.environ.get("ULTRON_CPU_STEPS", "500"))
LEARNING_RATE = float(os.environ.get("ULTRON_LR", "3e-4"))
WEIGHT_DECAY = 0.01
SAVE_EVERY = 250
EVAL_EVERY = 100
EVAL_BATCHES = 10
SEED = 42


def get_batch(data, device):
    if len(data) <= BLOCK_SIZE + 1:
        raise ValueError("Dataset split is too small for the configured block size.")
    ix = torch.randint(0, len(data) - BLOCK_SIZE - 1, (BATCH_SIZE,))
    x = torch.stack([data[i:i + BLOCK_SIZE] for i in ix])
    y = torch.stack([data[i + 1:i + BLOCK_SIZE + 1] for i in ix])
    return x.to(device), y.to(device)


@torch.no_grad()
def estimate_loss(model, train_data, val_data, device):
    model.eval()
    out = {}
    for name, data in (("train", train_data), ("val", val_data)):
        losses = []
        for _ in range(EVAL_BATCHES):
            xb, yb = get_batch(data, device)
            _, loss = model(xb, yb)
            losses.append(loss.item())
        out[name] = sum(losses) / len(losses)
    model.train()
    return out


def save_checkpoint(model, tokenizer, device, step, total_steps, best_val):
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
    torch.save(checkpoint, OUT / "ultron_v0_3.pt")
    (OUT / "training_info_v0_3.json").write_text(
        json.dumps({
            "version": "v0.3",
            "step": step,
            "total_steps": total_steps,
            "device": device,
            "dataset": str(DATA),
            "block_size": BLOCK_SIZE,
            "batch_size": BATCH_SIZE,
            "n_embd": N_EMBD,
            "n_head": N_HEAD,
            "n_layer": N_LAYER,
            "learning_rate": LEARNING_RATE,
            "weight_decay": WEIGHT_DECAY,
            "best_val_loss": best_val,
        }, indent=2),
        encoding="utf-8",
    )
    tokenizer.save(OUT / "tokenizer_v0_3.json")
    print(f"CHECKPOINT SAVED: step={step} val={best_val:.4f}", flush=True)


def main():
    torch.manual_seed(SEED)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(SEED)

    text = DATA.read_text(encoding="utf-8") + "\n\n" + DIALOGUE.read_text(encoding="utf-8")
    if len(text) < (BLOCK_SIZE + 2) * 2:
        raise ValueError("Training text is too small for v0.3.")

    tokenizer = CharTokenizer(text)
    ids = torch.tensor(tokenizer.encode(text), dtype=torch.long)

    split = int(0.90 * len(ids))
    train_data, val_data = ids[:split], ids[split:]

    if len(val_data) <= BLOCK_SIZE + 1:
        raise ValueError("Validation split is too small.")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    total_steps = GPU_STEPS if device == "cuda" else CPU_STEPS

    model = UltronTransformer(
        tokenizer.vocab_size,
        block_size=BLOCK_SIZE,
        n_embd=N_EMBD,
        n_head=N_HEAD,
        n_layer=N_LAYER,
        dropout=DROPOUT,
    ).to(device)

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
    )

    print(f"ULTRON v0.3 | device={device} | vocab={tokenizer.vocab_size}", flush=True)
    print(f"Model: {N_LAYER} layers | {N_EMBD} hidden | block {BLOCK_SIZE}", flush=True)
    print(f"Training: {total_steps} steps", flush=True)

    best_val = float("inf")
    started = time.time()

    for step in range(1, total_steps + 1):
        xb, yb = get_batch(train_data, device)
        _, loss = model(xb, yb)

        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()

        if step == 1 or step % EVAL_EVERY == 0:
            metrics = estimate_loss(model, train_data, val_data, device)
            best_val = min(best_val, metrics["val"])
            print(
                f"step {step:5d}/{total_steps} | "
                f"train {metrics['train']:.4f} | val {metrics['val']:.4f}",
                flush=True,
            )

        if step % SAVE_EVERY == 0:
            save_checkpoint(model, tokenizer, device, step, total_steps, best_val)

    save_checkpoint(model, tokenizer, device, total_steps, total_steps, best_val)
    print(f"ULTRON v0.3 COMPLETE in {(time.time() - started) / 60:.1f} minutes", flush=True)


if __name__ == "__main__":
    main()
