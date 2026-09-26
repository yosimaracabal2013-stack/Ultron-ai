"""Train ULTRON v0.2 from the expanded dataset."""

from pathlib import Path
import json
import torch
from tokenizer import CharTokenizer
from model import UltronTransformer

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "train.txt"
OUT = ROOT / "checkpoints"
OUT.mkdir(exist_ok=True)

BLOCK_SIZE = 128
BATCH_SIZE = 16
N_EMBD = 128
N_HEAD = 4
N_LAYER = 4
DROPOUT = 0.1
GPU_STEPS = 1000
CPU_STEPS = 300
LEARNING_RATE = 3e-4
SAVE_EVERY = 100


def get_batch(data, device):
    ix = torch.randint(0, len(data) - BLOCK_SIZE - 1, (BATCH_SIZE,))
    x = torch.stack([data[i:i + BLOCK_SIZE] for i in ix])
    y = torch.stack([data[i + 1:i + BLOCK_SIZE + 1] for i in ix])
    return x.to(device), y.to(device)


def save_checkpoint(model, tokenizer, device, step, total_steps):
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
    torch.save(checkpoint, OUT / "ultron_v0_2.pt")
    (OUT / "training_info_v0_2.json").write_text(
        json.dumps({
            "version": "v0.2",
            "steps": step,
            "total_steps": total_steps,
            "device": device,
            "mode": "expanded-dataset",
            "dataset": str(DATA),
        }, indent=2),
        encoding="utf-8",
    )
    print(f"CHECKPOINT SAVED at step {step}: {OUT / 'ultron_v0_2.pt'}", flush=True)


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

    tokenizer.save(OUT / "tokenizer_v0_2.json")
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
    optimizer = torch.optim.AdamW( model.parameters(), lr=LEARNING_RATE)

    print(f"ULTRON v0.2 | device={device} | vocab={tokenizer.vocab_size}", flush=True)
    print(f"Model: {N_LAYER} layers, {N_EMBD} hidden, block {BLOCK_SIZE}", flush=True)
    print(f"Training for {total_steps} steps...", flush=True)

    for step in range(1, total_steps + 1):
        model.train()
        xb, yb = get_batch(train_data, device)
        _, loss = model(xb, yb)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()

        if step == 1 or step % 25 == 0:
            model.eval()
            with torch.no_grad():
                vx, vy = get_batch(val_data, device)
                _, vloss = model(vx, vy)
            print(
                f"step {step:4d}/{total_steps} | train {loss.item():.4f} | val {vloss.item():.4f}",
                flush=True,
            )

        if step % SAVE_EVERY == 0:
            save_checkpoint(model, tokenizer, device, step, total_steps)

    save_checkpoint(model, tokenizer, device, total_steps, total_steps)
    print("ULTRON v0.2 TRAINING COMPLETE.", flush=True)


if __name__ == "__main__":
    main()
