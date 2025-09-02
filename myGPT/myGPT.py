#!/usr/bin/env python3
"""
Minimal GPT-style language model trainer and sampler.
Trains on a plain text file using byte-level tokens (0–255).
This code is compatible with Python 3.10+
"""

import argparse
import math
import os
import time
from dataclasses import dataclass

import torch
import torch.nn as nn
from torch.nn import functional as F


# ---------- Tokenizer (byte-level: no external deps) ----------
class ByteTokenizer:
    def __init__(self) -> None:
        self.vocab_size = 256

    def encode(self, s: str) -> torch.Tensor:
        return torch.tensor(list(s.encode("utf-8")), dtype=torch.long)

    def decode(self, ids: torch.Tensor) -> str:
        ids = ids.detach().cpu().tolist()
        return bytes(ids).decode("utf-8", errors="ignore")


# ---------- Data loader ----------
class TextDataset:
    def __init__(self, path: str, block_size: int, device: torch.device) -> None:
        self.device = device
        self.block_size = block_size
        with open(path, "rb") as f:
            self.data = torch.tensor(list(f.read()), dtype=torch.long)

    def get_batch(self, batch_size: int) -> tuple[torch.Tensor, torch.Tensor]:
        ix = torch.randint(0, len(self.data) - self.block_size - 1, (batch_size,))
        x = torch.stack([self.data[i : i + self.block_size] for i in ix]).to(self.device)
        y = torch.stack([self.data[i + 1 : i + 1 + self.block_size] for i in ix]).to(
            self.device
        )
        return x, y


# ---------- Model ----------
@dataclass
class GPTConfig:
    vocab_size: int = 256
    block_size: int = 256
    n_layer: int = 8
    n_head: int = 8
    n_embd: int = 512
    dropout: float = 0.1


class CausalSelfAttention(nn.Module):
    def __init__(self, cfg: GPTConfig) -> None:
        super().__init__()
        assert cfg.n_embd % cfg.n_head == 0
        self.n_head = cfg.n_head
        self.head_dim = cfg.n_embd // cfg.n_head
        self.key = nn.Linear(cfg.n_embd, cfg.n_embd, bias=False)
        self.query = nn.Linear(cfg.n_embd, cfg.n_embd, bias=False)
        self.value = nn.Linear(cfg.n_embd, cfg.n_embd, bias=False)
        self.proj = nn.Linear(cfg.n_embd, cfg.n_embd, bias=False)
        self.attn_drop = nn.Dropout(cfg.dropout)
        self.resid_drop = nn.Dropout(cfg.dropout)
        self.register_buffer(
            "mask",
            torch.triu(torch.ones(cfg.block_size, cfg.block_size), diagonal=1).bool(),
            persistent=False,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B, T, C = x.size()
        k = self.key(x).view(B, T, self.n_head, self.head_dim).transpose(1, 2)
        q = self.query(x).view(B, T, self.n_head, self.head_dim).transpose(1, 2)
        v = self.value(x).view(B, T, self.n_head, self.head_dim).transpose(1, 2)
        att = (q @ k.transpose(-2, -1)) / math.sqrt(self.head_dim)
        att = att.masked_fill(self.mask[:T, :T], float("-inf"))
        att = F.softmax(att, dim=-1)
        att = self.attn_drop(att)
        y = att @ v
        y = y.transpose(1, 2).contiguous().view(B, T, C)
        y = self.resid_drop(self.proj(y))
        return y


class MLP(nn.Module):
    def __init__(self, cfg: GPTConfig) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(cfg.n_embd, 4 * cfg.n_embd),
            nn.GELU(),
            nn.Linear(4 * cfg.n_embd, cfg.n_embd),
            nn.Dropout(cfg.dropout),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class Block(nn.Module):
    def __init__(self, cfg: GPTConfig) -> None:
        super().__init__()
        self.ln1 = nn.LayerNorm(cfg.n_embd)
        self.attn = CausalSelfAttention(cfg)
        self.ln2 = nn.LayerNorm(cfg.n_embd)
        self.mlp = MLP(cfg)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.attn(self.ln1(x))
        x = x + self.mlp(self.ln2(x))
        return x


class GPT(nn.Module):
    def __init__(self, cfg: GPTConfig) -> None:
        super().__init__()
        self.cfg = cfg
        self.tok_emb = nn.Embedding(cfg.vocab_size, cfg.n_embd)
        self.pos_emb = nn.Embedding(cfg.block_size, cfg.n_embd)
        self.drop = nn.Dropout(cfg.dropout)
        self.blocks = nn.ModuleList([Block(cfg) for _ in range(cfg.n_layer)])
        self.ln_f = nn.LayerNorm(cfg.n_embd)
        self.head = nn.Linear(cfg.n_embd, cfg.vocab_size, bias=False)
        self.apply(self._init_weights)

    def _init_weights(self, module: nn.Module) -> None:
        if isinstance(module, (nn.Linear, nn.Embedding)):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
        if isinstance(module, nn.Linear) and module.bias is not None:
            nn.init.zeros_(module.bias)

    def forward(self, idx: torch.Tensor, targets: torch.Tensor | None = None):
        B, T = idx.size()
        pos = torch.arange(0, T, device=idx.device, dtype=torch.long).unsqueeze(0)
        x = self.tok_emb(idx) + self.pos_emb(pos)
        x = self.drop(x)
        for block in self.blocks:
            x = block(x)
        x = self.ln_f(x)
        logits = self.head(x)
        loss = None
        if targets is not None:
            loss = F.cross_entropy(
                logits.view(B * T, -1), targets.view(B * T), ignore_index=-1
            )
        return logits, loss

    @torch.no_grad()
    def generate(
        self, idx: torch.Tensor, max_new_tokens: int, temperature: float = 1.0, top_k: int | None = None
    ) -> torch.Tensor:
        self.eval()
        for _ in range(max_new_tokens):
            idx_cond = idx[:, -self.cfg.block_size :]
            logits, _ = self(idx_cond)
            logits = logits[:, -1, :] / max(temperature, 1e-6)
            if top_k is not None:
                v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                logits[logits < v[:, [-1]]] = -float("inf")
            probs = F.softmax(logits, dim=-1)
            next_id = torch.multinomial(probs, num_samples=1)
            idx = torch.cat((idx, next_id), dim=1)
        return idx


# ---------- Training ----------
def train(
    data_path: str,
    out_dir: str,
    steps: int,
    batch_size: int,
    block_size: int,
    n_layer: int,
    n_head: int,
    n_embd: int,
    lr: float,
    dropout: float,
    eval_every: int,
    device: str,
) -> None:
    torch.manual_seed(1337)
    dev = torch.device(device if torch.cuda.is_available() or "mps" in device else "cpu")

    os.makedirs(out_dir, exist_ok=True)
    tok = ByteTokenizer()
    ds = TextDataset(data_path, block_size, dev)

    cfg = GPTConfig(
        vocab_size=tok.vocab_size,
        block_size=block_size,
        n_layer=n_layer,
        n_head=n_head,
        n_embd=n_embd,
        dropout=dropout,
    )
    model = GPT(cfg).to(dev)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, betas=(0.9, 0.95), weight_decay=0.1)

    best_loss = float("inf")
    t0 = time.time()
    for step in range(1, steps + 1):
        model.train()
        x, y = ds.get_batch(batch_size)
        _, loss = model(x, y)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()

        if step % eval_every == 0 or step == steps:
            model.eval()
            with torch.no_grad():
                vx, vy = ds.get_batch(batch_size)
                _, vloss = model(vx, vy)
            msg = (
                f"step {step}/{steps} | train_loss {loss.item():.4f} "
                f"| val_loss {vloss.item():.4f} | elapsed {time.time() - t0:.1f}s"
            )
            print(msg, flush=True)
            t0 = time.time()

            if vloss.item() < best_loss:
                best_loss = vloss.item()
                ckpt_path = os.path.join(out_dir, "gpt_byte.pt")
                torch.save(
                    {
                        "model": model.state_dict(),
                        "cfg": cfg.__dict__,
                    },
                    ckpt_path,
                )

    # quick sample
    start = torch.randint(0, 256, (1, 1), device=dev, dtype=torch.long)
    sample = model.generate(start, max_new_tokens=400, temperature=1.0, top_k=200)[0]
    print(ByteTokenizer().decode(sample))


# ---------- CLI ----------
def main() -> None:
    p = argparse.ArgumentParser(description="Train a tiny GPT on a text file.")
    p.add_argument("--data", type=str, required=True, help="Path to .txt training data")
    p.add_argument("--out", type=str, default="out", help="Checkpoint directory")
    p.add_argument("--steps", type=int, default=2000)
    p.add_argument("--batch", type=int, default=32)
    p.add_argument("--block", type=int, default=256)
    p.add_argument("--layers", type=int, default=8)
    p.add_argument("--heads", type=int, default=8)
    p.add_argument("--emb", type=int, default=512)
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--dropout", type=float, default=0.1)
    p.add_argument("--eval_every", type=int, default=100)
    p.add_argument(
        "--device",
        type=str,
        default="cuda",
        choices=["cuda", "cpu", "mps"],
        help="Preferred device",
    )
    args = p.parse_args()

    train(
        data_path=args.data,
        out_dir=args.out,
        steps=args.steps,
        batch_size=args.batch,
        block_size=args.block,
        n_layer=args.layers,
        n_head=args.heads,
        n_embd=args.emb,
        lr=args.lr,
        dropout=args.dropout,
        eval_every=args.eval_every,
        device=args.device,
    )


if __name__ == "__main__":
    main()
