# ULTRON Brain v0.1

This directory contains ULTRON's first from-scratch language-model training foundation.

## What this is
- A character-level tokenizer written from scratch.
- A small decoder-only Transformer written in PyTorch.
- A training script that learns next-token prediction from plain text.
- A generation script for testing a trained checkpoint.

This is intentionally a small learning model. It is not expected to match large commercial AI systems. The purpose of v0.1 is to prove that ULTRON can have its own trainable model rather than relying on an external chat API.

## Training
Run from the repository root:

```bash
pip install -r ai/requirements.txt
python ai/train.py
```

The default training data is `ai/data/train.txt`. The script writes checkpoints to `ai/checkpoints/`.

## Generation
After training:

```bash
python ai/generate.py --prompt "ULTRON:"
```

Never put API keys or other secrets in this repository.
