# ULTRON v0.1 — Google Colab training notebook

This notebook trains ULTRON's from-scratch Transformer in Google Colab.

## One-click setup
1. Open this notebook in Google Colab.
2. In Colab, choose a GPU runtime if one is available: Runtime → Change runtime type → GPU.
3. Run the cells from top to bottom.

The notebook clones the ULTRON repository, installs PyTorch, trains the model, tests generation, and optionally downloads the checkpoint.

No ChatGPT, Claude, Gemini, or other model API is used for training.

---

### Cell 1 — Clone ULTRON

```python
!git clone https://github.com/yosimaracabal2013-stack/Ultron-ai.git
%cd Ultron-ai
!git checkout ultron-brain-v0.1
```

### Cell 2 — Install dependencies and verify the device

```python
!pip -q install -r ai/requirements.txt

import torch
print("PyTorch:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))
else:
    print("No GPU detected — training will use CPU and may be slow.")
```

### Cell 3 — Train ULTRON

```python
!python ai/train.py
```

### Cell 4 — Test ULTRON

```python
!python ai/generate.py --prompt "ULTRON:" --tokens 300
```

### Cell 5 — Try your own prompt

```python
prompt = "USER: What is your purpose?\nULTRON:"
!python ai/generate.py --prompt "$prompt" --tokens 200
```

### Cell 6 — Download the trained brain

```python
from google.colab import files
files.download("ai/checkpoints/ultron_v0_1.pt")
```

### Important
The current v0.1 dataset is intentionally tiny. The first training run is a proof that ULTRON can train and generate text from its own learned weights. The next major step is expanding the dataset and improving the training pipeline.
