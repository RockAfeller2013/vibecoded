# TinyGPT

A minimal GPT-style language model implemented in PyTorch.  
Trains on raw text using byte-level tokenization (0–255).  
Intended for learning and experimentation, not production.

---

## Features
- Byte-level tokenizer (no external dependencies)
- GPT architecture with:
  - Token and positional embeddings
  - Multi-head masked self-attention
  - Feedforward MLP blocks
  - Layer normalization and residual connections
- AdamW optimizer with gradient clipping
- Autoregressive text generation
- Configurable model size, depth, and training hyperparameters
- PyTorch-based, compatible with Python 3.10+

# Hardware

- https://www.hyperscalers.com.au/about-us-hyperscale
- 
---

## Requirements
- Python 3.10+
- PyTorch

Install dependencies:
```bash
pip install torch

Usage
Training

Prepare a plain text file input.txt.
Run training:

python tinygpt.py --data input.txt --steps 5000 --batch 32 --block 256


Optional arguments:

--out checkpoint directory (default: out)

--layers number of transformer blocks

--heads number of attention heads

--emb embedding dimension

--lr learning rate

--dropout dropout rate

--device cuda, cpu, or mps

Sampling

After training, the script generates text automatically.
Sample output is printed at the end of training.

Example
python tinygpt.py --data tiny_shakespeare.txt --steps 2000 --batch 64 --layers 6 --heads 8 --emb 256


Output (example):

step 2000/2000 | train_loss 1.9432 | val_loss 2.1012 | elapsed 4.3s
And I say to thee, my lord, let us away into the night...

Checkpoints

Best model is saved automatically to:

out/gpt_byte.pt

Notes

This is a teaching/learning implementation.

For serious use, see nanoGPT
.

Larger models require significant GPU resources.
